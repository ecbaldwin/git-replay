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

## Scripts

### git-replay

File: `git_replay/main.py`

This is the script that you call from your repo to make it all work. There are
sub-commands to initialize repositories, push and fetch between repos, and to
help merge when a conflict in the predecessor graph is found.

Since the transport mechanisms don't understand the predecessor graph, I needed
to provide a new command to wrap them. The new command uses the
`refs/tags/predecessor/<commit id>` tags to facilitate moving intermediate
commits.

Sub-Command          | Description
-------------------- | -----------
init                 | Copy hooks into a local working repo. Run it locally.
init-server          | Copy server-side hooks into a repo. Run it on the server repo.
id                   | Find the change id from a commit by following the predecessor graph.
push                 | Push changes to a repo. Uses tags to send intermediates to the server.
fetch-intermediates  | Fetch missing intermediate commits from a server. Uses tags.
merge                | Merges divergent predecessor graphs when a conflict is discovered.

## Hooks

Hook         | Where  | File                         | Description
------------ | ------ | ---------------------------- | --------------
post-rewrite | Client | `git_replay/post_rewrite.py` | Creates new commits with pointers to old commits.
post-receive | Server | `git_replay/post_receive.py` | Cleans up "magic" refs.
update       | Server | `git_replay/update.py`       | Handles pushes. Ensures safe updates to changes. Pushes upstream.

### post-rewrite

Run after any rebase or commit --amend operation. Writes new new references
which contain pointers to the old references. The intermediate new references,
the ones created by the rebase or amend command, but before calling this hook,
get orphaned.

The old commits would also be orphaned except that this hook creates a tag in
`refs/tags/predecessors/<commit id>` pin them in the repo. If `git gc` and the
various transport mechanisms eventually get modified to follow predecessor
references then these tags will no longer be necessary.

### post-receive

Cleans up "magic" refs. These are pass through refs. Many unrelated changes
come in through them so they get forced pushed and the old values don't matter.

### update

This is the meaty hook on the server side which rejects changes when the
predecessor graph diverges.

TODO: It will also move changes up to the upstream server when they are accepted.

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

### Server-

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
