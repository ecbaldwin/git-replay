import functools
import git
import os
import shutil
import stat
import subprocess
import sys

from git_replay import change
from git_replay import lib


HOOKS_DIR = "hooks"
POST_REWRITE_FILENAME = "post-rewrite"
PRE_RECEIVE_FILENAME = "pre-receive"
UPDATE_FILENAME = "update"


class UsageException(Exception):
    """ Raised when the command is invoked improperly """


def require_repo(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            repo = git.Repo(".")
        except git.exc.InvalidGitRepositoryError:
            raise UsageException("This command should be run from inside a workspace to initialize")
        return f(repo, *args, **kwargs)
    return wrapper


def _copy_hook(repo, program_name, name):
    source = os.path.join(os.path.dirname(program_name),
                          name)
    destination = os.path.join(repo.git_dir, HOOKS_DIR, name)

    shutil.copyfile(source, destination)
    st = os.stat(destination)
    os.chmod(destination, st.st_mode | stat.S_IEXEC)


@require_repo
def command_id(repo, program_name, args):
    if len(args) == 0:
        args = ["HEAD"]
    for arg in args:
        c = change.Change(repo.commit(rev=arg))
        print(c.id)


def parse_push_args(repo, args):
    remote_name, refspec = args

    # For now, we're only allowing simple <src>:<dst> refspecs. The following
    # checks enforce that.
    if ":" not in refspec:
        raise UsageException("Only simple <src>:<dst> refspecs are allowed")
    if refspec.startswith("+"):
        raise UsageException("Forced pushes aren't allowed")
    if refspec == ":":
        raise UsageException("Deleting refs on the remote is not allowed")
    if refspec.startswith(":"):
        raise UsageException("Pushing all matching refs is not allowed")
    if refspec.endswith(":"):
        raise UsageException("Destination is missing")

    src, dst = refspec.split(":", 1)
    return remote_name, src, dst


@require_repo
def command_push(repo, program_name, args):
    # git-replay push <remote> <refspec>
    remote_name, src_ref, dst_ref = parse_push_args(repo, args)
    reference = lib.map_to_upstream_branch(dst_ref)
    if reference.startswith("refs/heads/"):
        reference = reference[11:]

    local = repo.commit(src_ref)
    remote = repo.commit(reference)

    # Get changes as seen on the local and remote branches respectively.
    local_changes = change.Changes.from_range(repo, remote, local)
    remote_changes = change.Changes.from_range(repo, local, remote)

    push_commits = set()
    for local_change, remote_change in local_changes & remote_changes:
        if remote_change not in local_change:
            raise change.Conflict()
        push_commits.update(local_change - remote_change)

    for c in local_changes - remote_changes:
        push_commits.update(c)

    # Subtract commits reachable on local branch without following predecessors
    no_tags = set(repo.iter_commits("%s..%s" % (remote, local)))
    push_commits -= no_tags

    cmd = ["git", "push", remote_name]
    cmd.extend("predecessors/%s" % c for c in push_commits)
    cmd.append("+%s" % args[1])
    subprocess.run(cmd, check=True)


@require_repo
def command_fetch_intermediates(repo, program_name, args):
    """ Fetches intermediate commits reachable through predecessor refs

    Since the git transfer protocols don't understand these references, the
    local repo is often left without some intermediate commits after fetching.
    Those commits are important to link the whole history of a change.
    """
    # git-replay fetch-intermediates <remote> <reference branch>
    remote_name, commit_range = args

    while True:
        try:
            changes = change.Changes.from_commit_range(repo, commit_range)
            break
        except change.IncompleteChanges as e:
            cmd = ["git", "fetch", remote_name]
            cmd.extend("predecessors/%s" % c.decode("ascii") for c in e.missing_commits)
            subprocess.run(cmd, check=True)

    for c in changes:
        print(c)


@require_repo
def command_init(repo, program_name, args):
    _copy_hook(repo, program_name, POST_REWRITE_FILENAME)


@require_repo
def command_init_server(repo, program_name, args):
    _copy_hook(repo, program_name, PRE_RECEIVE_FILENAME)
    _copy_hook(repo, program_name, UPDATE_FILENAME)


def dispatch_command(program_name, args):
    if len(args) == 0:
        raise UsageException("Command is missing")

    command = args[0]
    if command == "init":
        return command_init(program_name, args[1:])

    if command == "init-server":
        return command_init_server(program_name, args[1:])

    if command == "id":
        return command_id(program_name, args[1:])

    if command == "push":
        return command_push(program_name, args[1:])

    if command == "fetch-intermediates":
        return command_fetch_intermediates(program_name, args[1:])

    raise UsageException("Command not recognized: %s" % command)


def main():
    program_name = sys.argv[0]
    try:
        dispatch_command(program_name, sys.argv[1:])
    except UsageException as e:
        print(e)
        # TODO Print some generic usage message along with the specific message
        sys.exit(1)
