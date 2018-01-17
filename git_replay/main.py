import functools
import git
import os
import shutil
import stat
import subprocess
import sys

from git_replay import change


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

    src_ref, dst_ref = refspec.split(":", 1)
    remote_ref = "%s/%s" % (remote_name, dst_ref)

    return remote_name, repo.commit(rev=src_ref), repo.commit(rev=remote_ref)


@require_repo
def command_push(repo, program_name, args):
    # git-replay push <remote> <refspec>
    remote_name, src, dst = parse_push_args(repo, args)

    # Get changes as seen on the local and remote branches respectively.
    src_changes = change.Changes.from_range(repo, dst, src)
    dst_changes = change.Changes.from_range(repo, src, dst)

    for src_change, dst_change in src_changes & dst_changes:
        if dst_change not in src_change:
            raise change.Conflict()

    cmd = ["git", "push", remote_name, "+%s" % args[1]]
    subprocess.run(cmd, check=True)


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

    if command == "push":
        return command_push(program_name, args[1:])

    raise UsageException("Command not recognized: %s" % command)


def main():
    program_name = sys.argv[0]
    try:
        dispatch_command(program_name, sys.argv[1:])
    except UsageException as e:
        print(e)
        # TODO Print some generic usage message along with the specific message
        sys.exit(1)
