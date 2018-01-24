import git
import sys

from git_replay import change
from git_replay import lib


HEADS = "refs/heads/"
CHANGE_HEADS = "refs/changes/"


class ReferenceNotInHeads(Exception):
    """ Raised when the ref being updated is not in refs/heads/ """
    # This is probably ok. I just want to see where it comes up.


def get_change_branch(upstream, change_id):
    return "%s%s/%s" % (CHANGE_HEADS, upstream[len(HEADS):], change_id)


def check_branch(repo, reference, old_ref, new_ref):
    reference = lib.map_to_upstream_branch(reference)

    if not reference.startswith(HEADS):
        raise ReferenceNotInHeads()

    # Get changes as seen on the local and remote branches respectively.
    try:
        client_changes = change.Changes.from_range(repo, reference, new_ref)
    except git.exc.GitCommandError:
        # The branch doesn't exist yet. Just return, allowing the update.
        return

    update_changes = []
    for client_change in client_changes:
        try:
            server_commit = repo.commit(rev=get_change_branch(reference,
                                                              client_change.id))
        except git.exc.BadName:
            # Don't have this change in the context of this branch yet
            update_changes.append(client_change)
            continue

        server_change = change.Change(server_commit)
        if server_change not in client_change:
            raise change.Conflict()
        if client_change not in server_change:
            update_changes.append(client_change)

    for c in update_changes:
        git.refs.symbolic.SymbolicReference.create(repo=repo,
                                                   path=get_change_branch(reference, c.id),
                                                   reference=c.head,
                                                   force=True)


def main():
    reference, old_ref, new_ref = sys.argv[1:4]

    # Some environment variables that might be of interest
    # PWD - On the server's bare repo, this is the repo directory
    # GIT_DIR - On the server's bare repo, this is '.'
    check_branch(git.Repo("."), reference, old_ref, new_ref)
