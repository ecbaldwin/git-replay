import git
import sys


def check_updates(repo, updates):
    updates = [(repo.commit(rev=old), repo.commit(rev=new), ref_name)
               for old, new, ref_name in updates]

    for old, new, ref_name in updates:
        print("Checking update %s -> %s in %s" % (old, new, ref_name))

    return True


def main():
    # Some environment valiable that might be of interest
    # PWD - On the server's bare repo, this is the repo directory
    # GIT_DIR - On the server's bare repo, this is '.'
    # GIT_PUSH_OPTION_COUNT - How much push options are sent
    # GIT_ALTERNATE_OBJECT_DIRECTORIES - points to the repo's object dir
    # GIT_OBJECT_DIRECTORY - points to a quarantine directory
    # GIT_QUARANTINE_PATH - seems to be the same os the previous
    repo = git.Repo(".")

    # Git feeds refs to be updated per line like below.
    #
    #     old_commit_hash new_commit_hash refs/../ref_name
    #
    if not check_updates(repo, [line.split() for line in sys.stdin]):
        sys.exit(1)
