# Git Replaces

This repo contains a proof of concept for my git replay idea. The goal
is to keep around the history of a patch that goes through many `git
--amend` and `git rebase` revisions before it is finally merged into a
public branch somewhere. Enough history needs to be kept so that when
conflicts arise, the divergence will be detected and git will have the
information to do a merge between the two. When a patch is rebased or
amend independently in two different workspaces, git doesn't detect the
conflict and it can be difficult to merge them together. This aims to
solve this problem.

This essentially gives us rebase-like control over exactly how the final
branch will look while at the same time making it as safe as branching
and merging. It is the best of both worlds.

It keeps more commits which could bloat the repository a bit. However,
some code review server repos are keeping around this information
anyway, just in a more out-of-band manner. The extra commits are hidden
from the mainline history in a side history. A separate connected graph
would exist in the side-history for each change.

# The Plan

Here's the plan for the proof of concept. It has a few warts most (if
not all) of which can be solved by implementing this in core git. For
now, we need to prove its worth.

## Server Side

Setup an intermediate server which will accept pushes, prepare the
entire thing and then forward it onto the gerrit or github server
upstream. It will use server side hooks to fire everything off.

The intermediate server will sync merges from upstream.

Editing through the github or gerrit UIs won't work right because it
won't create a predecessor reference in the commit. Just need to let
people know that this is not a safe thing to do.

### Open questions

- How can we avoid accidental pushes directly to the upstream server?

  If we have control over the gerrit server, we can block access to the
  port from anywhere but the intermediate server.

- Can I use ssh-agent forwarding to allow submission upstream?

  Just need to try this.

## Client side

Use the post-rewrite hooks to update all of the rewrites with
predecessor references.

Need to implement all of the merging, squashing, and stuff here.

# References

My thread on the git mailing list (I got a little frustrated with it)
- https://marc.info/?t=151400952500001&r=1&w=2

Laurent Charignon's blog about changset evolution in mercurial
- https://blog.laurentcharignon.com/post/2016-02-02-changeset-evolution/
- Other related links:
  - https://www.mercurial-scm.org/wiki/EvolveExtension
  - https://www.mercurial-scm.org/wiki/ChangesetEvolutionDevel

Git series
- https://github.com/git-series/git-series
  - I haven't seen any collaborative features in this. It seems to just
    track and prepare emails.

Git hooks
- https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
  - Look at the post-rewrite hook especially
  - Maybe look at:
    pre-push
  - Can we run server side hooks or gerrit or github? I doubt it.
    - Someone can force push to github and still clobber stuff
    - For github, maybe I can do a webhook or something to detect

# Terminology

* change:

    > The collection of revisions that from the history of what is to
    > end up being a single commit in the git history.

* predecessor:

    > A change from which the current commit was derived before doing an
    > amend or rebase.
