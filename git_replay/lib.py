REPLACE_MAX = 1


def map_to_upstream_branch(branch):
    if branch.startswith("refs/for/"):
        return branch.replace("/for/", "/heads/", REPLACE_MAX)

    # TODO(Carl) Without magic refs, is there a way to map? For example, in
    # github, can be look at the PR target branch or something? The advantage
    # of being able to map to an upstream branch is that we could enforce
    # change consistency between different PRs. For example, one PR might build
    # from another. It would be very beneficial to be able to detect rebases
    # across them.

    return branch
