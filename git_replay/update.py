import git
import sys

from git_replay import change
from git_replay import lib


HEADS = "refs/heads/"
TAGS = "refs/tags/"
CHANGE_HEADS = "refs/changes/"


class ReferenceNotInHeads(Exception):
    """ Raised when the ref being updated is not in refs/heads/ """
    # This is probably ok. I just want to see where it comes up.


def get_change_branch(upstream, change_id):
    return "%s%s/%s" % (CHANGE_HEADS, upstream[len(HEADS):], change_id)


def check_branch(repo, reference, old_ref, new_ref):
    reference = lib.map_to_upstream_branch(reference)

    # Allow updates to tags. Unchecked for now.
    if reference.startswith(TAGS):
        return

    if not reference.startswith(HEADS):
        raise ReferenceNotInHeads()

    # Get changes as seen on the local and remote branches respectively.
    try:
        client_changes = change.Changes.from_range(repo, reference, new_ref)
    except git.exc.GitCommandError:
        # The branch doesn't exist yet. Just return, allowing the update.
        return

    for client_change in client_changes:
        try:
            server_change = change.Change(
                repo.commit(
                    rev=get_change_branch(reference, client_change.id)))
        except git.exc.BadName:
            # Don't have this change in the context of this branch yet. No worries.
            server_change = change.Change()

        if server_change not in client_change:
            raise change.Conflict(server_change.id)

        if client_change in server_change:
            # The server is up to date on this change. Go to the next.
            continue

        # TODO(Carl) Each change is updated as soon as we verify that it is up
        # to date. Since there may be many changes, we could have some updated
        # while later ones don't get updated. I make no attempt to roll back
        # the ones which have been updated.
        # 1. For gerrit style code review, each change is independent. It isn't
        #    so bad that earlier changes may get updated while laters ones
        #    don't. I think it is acceptable.
        # 2. For github style code review, the branch won't get updated.
        #    Updates to the earlier changes will be unreachable from any branch
        #    until you fix up the entire branch and successfully update all of
        #    the changes in the branch. I should give some thought to updating
        #    all of the changes atomically.
        git.refs.symbolic.SymbolicReference.create(
            repo=repo,
            path=get_change_branch(reference, client_change.id),
            reference=client_change.head,
            force=True)


def main():
    reference, old_ref, new_ref = sys.argv[1:4]

    # Some environment variables that might be of interest
    # PWD - On the server's bare repo, this is the repo directory
    # GIT_DIR - On the server's bare repo, this is '.'
    check_branch(git.Repo("."), reference, old_ref, new_ref)
