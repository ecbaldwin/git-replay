import git
import sys

from git_replay import change


class DropNotImplemented(Exception):
    """ Raised when trying to drop a change from the server """

    # This might be okay. I just want to see the situations where it comes up
    # and give it some thought before allowing it.


def main():
    reference, old_ref, new_ref = sys.argv[1:4]

    if old_ref == "0000000000000000000000000000000000000000":
        return

    # Some environment variables that might be of interest
    # PWD - On the server's bare repo, this is the repo directory
    # GIT_DIR - On the server's bare repo, this is '.'
    repo = git.Repo(".")

    # Get changes as seen on the local and remote branches respectively.
    client_changes = change.Changes.from_range(repo, old_ref, new_ref)
    server_changes = change.Changes.from_range(repo, new_ref, old_ref)

    if server_changes - client_changes:
        raise DropNotImplemented()

    for server_change, client_change in server_changes & client_changes:
        if server_change not in client_change:
            raise change.Conflict()
