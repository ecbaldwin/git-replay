class Conflict(Exception):
    """ Raised when trying to push a change that isn't a superset of the remote """


class Change:
    def __init__(self, commit):
        self.chain = self._get_chain(commit)

    @staticmethod
    def _get_chain(commit):
        """ Follows the entire chain of commits building a list from earliest to latest"""
        # TODO(Carl) Chain will not always be linear. In general, it will be a DAG.
        chain = []

        def build(commit):
            if commit.predecessors:
                # The presence of more than one predecessor means other changes
                # were merged into this one.
                if 1 < len(commit.predecessors):
                    raise NotImplementedError("Cannot yet handle multiple predecessors")

                # Commits in the same change are reachable through the first
                # predecessor.
                build(commit.predecessors[0])

            chain.append(commit)
            return chain
        return build(commit)

    @property
    def id(self):
        """ The id of the change is the id of the very first commit that started it. """
        return str(self.chain[0])

    @property
    def head(self):
        """ The id of the head (most up to date) commit in the change. """
        return str(self.chain[-1])

    def __contains__(self, other):
        """ Returns True iff the other change is a subset of this one """
        length = len(other.chain)
        if len(self.chain) < length:
            return False

        return other.chain[length-1] == self.chain[length-1]

    def __str__(self):
        return "Change (%s)" % ", ".join([str(c)[:7] for c in self.chain])


class Changes:
    """ A collection of changes, like on a branch or in a range of commits """
    def __init__(self, commits):
        self._changes = {str(c.id): c for c in [Change(c) for c in commits]}
        self._set = set(self._changes)

    @classmethod
    def from_range(cls, repo, start, end):
        return cls(repo.iter_commits("%s..%s" % (start, end)))

    def __sub__(self, other):
        return [self._changes[str(i)] for i in self._set - other._set]

    def __and__(self, other):
        return [(self._changes[str(i)], other._changes[str(i)]) for i in self._set & other._set]

    def __iter__(self):
        for c in self._changes:
            yield self._changes[c]
