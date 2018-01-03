#!/usr/bin/env python

# Graphs the current branch of the current repo with predecessor references.
# This isn't really practical on most repos. But, for the small ones I've
# started testing on, it works fine.


import git
import sys


visited = set()


def visit_commit(commit):
    if commit in visited:
        return
    visited.add(commit)

    print("    \"%s\" [ label=\"%s\"; ]" % (commit, commit.summary))
    for parent in commit.parents:
        print("\"%s\" -> \"%s\"" % (commit, parent))
        visit_commit(parent)
    for predecessor in commit.predecessors:
        print("\"%s\" -> \"%s\" [ style=\"dashed\"; tooltip=\"%s\" ]" % (commit, predecessor, commit.summary))
        visit_commit(predecessor)


def main():
    print("digraph commits {")
    repo = git.Repo(".")
    visit_commit(repo.head.commit)
    print("}")
