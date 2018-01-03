import git
import sys

# TODO(Carl) What are the implications of amending/rebasing merge commits
# TODO(Carl) What happens to the GPG signature?
# TODO(Carl) Test amending the first commit

def convert_date(date, tz_offset):
    # GitPython docs define tz_offset as seconds west of utc, strange.
    sign = '-' if tz_offset > 0 else '+'
    return "%d %s%02d00" % (date, sign, abs(tz_offset / 3600))


def insert_references(repo, pairs):
    replacements = {}

    for old_rev, new_rev in pairs:
        old, new = repo.commit(rev=old_rev), repo.commit(rev=new_rev)

        # Map the commit's parents to commits that we've already replaced
        new_parents = [replacements.get(p, p) or p for p in new.parents]

        author_date = convert_date(new.authored_date, new.author_tz_offset)
        commit_date = convert_date(new.committed_date, new.committer_tz_offset)

        # Copy the old commit but add replaces references to the old commits
        new_new = git.objects.commit.Commit.create_from_tree(
            repo=repo,
            tree=new.tree,
            message=new.message,
            parent_commits=new_parents,
            head=False,
            author=new.author,
            committer=new.committer,
            author_date=author_date,
            commit_date=commit_date,
            predecessors=[old])

        replacements[new] = new_new

        # Create a tag to pin the replaced commit in the object store
        git.refs.tag.TagReference.create(
            repo,
            path="predecessors/%s" % old,
            ref=old,
            force=True)

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
