import git


class Conflict(Exception):
    """ Raised when trying to push a change that isn't a superset of the remote """


class IncompleteChange(Exception):
    """ Raised when trying to follow the chain of commits in a change and one cannot be found """
    def __init__(self, missing_commit):
        self.missing_commit = missing_commit


class IncompleteChanges(Exception):
    """ Raised when failing to create one or more changes due to missing commits """
    def __init__(self, missing_commits):
        self.missing_commits = missing_commits


class Change:
    def __init__(self, commit):
        self.chain = self._get_chain(commit)

    @staticmethod
    def _get_chain(commit):
        """ Follows the entire chain of commits building a list from earliest to latest"""
        # TODO(Carl) Chain will not always be linear. In general, it will be a DAG.
        chain = []

        def build(commit):
            try:
                predecessors = commit.predecessors
            except git.cmd.MissingObject as e:
                raise IncompleteChange(e.sha1)
            if predecessors:
                # The presence of more than one predecessor means other changes
                # were merged into this one.
                if 1 < len(predecessors):
                    raise NotImplementedError("Cannot yet handle multiple predecessors")

                # Commits in the same change are reachable through the first
                # predecessor.
                build(predecessors[0])

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

    def __sub__(self, other):
        common_length = min(len(self.chain), len(other.chain))
        for i in range(0, common_length):
            if self.chain[i] != other.chain[i]:
                return self.chain[i:]
        return self.chain[common_length:]

    def __iter__(self):
        for c in self.chain:
            yield c


class Changes:
    """ A collection of changes, like on a branch or in a range of commits """
    def __init__(self, commits):
        changes = []
        missing_commits = []
        for commit in commits:
            try:
                changes.append(Change(commit))
            except IncompleteChange as e:
                missing_commits.append(e.missing_commit)

        if missing_commits:
            raise IncompleteChanges(missing_commits)

        self._changes = {str(c.id): c for c in changes}
        self._set = set(self._changes)

    @classmethod
    def from_commit_range(cls, repo, commit_range):
        return cls(repo.iter_commits(commit_range))

    @classmethod
    def from_range(cls, repo, start, end):
        return cls.from_commit_range(repo, "%s..%s" % (start, end))

    def __sub__(self, other):
        return [self._changes[str(i)] for i in self._set - other._set]

    def __and__(self, other):
        return [(self._changes[str(i)], other._changes[str(i)]) for i in self._set & other._set]

    def __iter__(self):
        for c in self._changes:
            yield self._changes[c]
