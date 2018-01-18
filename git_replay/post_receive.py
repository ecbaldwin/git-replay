import git
import os
import sys


def check_updates(repo, updates):
    for old, new, ref_name in updates:
        if ref_name.startswith("refs/for/"):
            ref_file_name = os.path.join(repo.git_dir, ref_name)
            os.remove(ref_file_name)


def main():
    check_updates(git.Repo("."),
                  [line.split() for line in sys.stdin])
