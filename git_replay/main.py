import functools
import git
import os
import shutil
import stat
import sys


HOOKS_DIR = "hooks"
POST_REWRITE_FILENAME = "post-rewrite"


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


@require_repo
def command_init(repo, program_name, args):
    bin_dir = os.path.dirname(program_name)
    post_rewrite_script = os.path.join(bin_dir, POST_REWRITE_FILENAME)
    destination = os.path.join(repo.git_dir, HOOKS_DIR, POST_REWRITE_FILENAME)

    shutil.copyfile(post_rewrite_script, destination)
    st = os.stat(destination)
    os.chmod(destination, st.st_mode | stat.S_IEXEC)


def dispatch_command(program_name, args):
    if len(args) == 0:
        raise UsageException("Command is missing")

    command = args[0]
    if command == "init":
        return command_init(program_name, args[1:])

    raise UsageException("Command not recognized: %s" % command)


def main():
    program_name = sys.argv[0]
    try:
        dispatch_command(program_name, sys.argv[1:])
    except UsageException as e:
        print(e)
        # TODO Print some generic usage message along with the specific message
        sys.exit(1)
