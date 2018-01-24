import collections
import git
import sys

# TODO(Carl) What are the implications of amending/rebasing merge commits
# TODO(Carl) What happens to the GPG signature?
# TODO(Carl) Test amending the first commit


def convert_date(date, tz_offset):
    # GitPython docs define tz_offset as seconds west of utc, strange.
    sign = '-' if tz_offset > 0 else '+'
    return "%d %s%02d00" % (date, sign, abs(tz_offset / 3600))


def make_rebase_map(pairs):
    rebase_map = collections.defaultdict(list)
    for old, new in pairs:
        rebase_map[new].append(old)
    return dict(rebase_map)


def replace_commit(repo, commit, new_parents, predecessors):
    author_date = convert_date(commit.authored_date, commit.author_tz_offset)
    commit_date = convert_date(commit.committed_date, commit.committer_tz_offset)

    return git.objects.commit.Commit.create_from_tree(
        repo=repo,
        tree=commit.tree,
        author=commit.author,
        committer=commit.committer,
        message=commit.message,

        parent_commits=new_parents,
        author_date=author_date,
        commit_date=commit_date,
        predecessors=predecessors)


def insert_references(repo, pairs):
    pairs = [(repo.commit(rev=old), repo.commit(rev=new)) for old, new in pairs]

    rebase_map = make_rebase_map(pairs)

    replacements = {}
    for old, new in pairs:
        # Create a tag to pin the replaced commit in the object store
        git.refs.tag.TagReference.create(
            repo,
            path="predecessors/%s" % old,
            ref=old,
            force=True)

        if replacements.get(new):
            continue

        # Copy the old commit but add replaces references to the old commits
        new_new = replace_commit(repo,
                                 commit=new,
                                 new_parents=[replacements.get(p, p) or p for p in new.parents],
                                 predecessors=rebase_map[new])

        replacements[new] = new_new

    # Reset the head to the new chain of commits
    repo.head.reset(new_new, index=False)


def main():
    # Find the git repo given the current working directory just like git does.
    repo = git.Repo(".")

    # Git feeds pairs of rewritten commits one per line like below. They come
    # in order from parent to child.
    #
    #     old_commit_hash new_commit_hash
    #
    insert_references(repo, [line.split() for line in sys.stdin])
