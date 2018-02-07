export GIT_AUTHOR_NAME="Test Author"
export GIT_AUTHOR_EMAIL="author@example.com"
export GIT_COMMITTER_NAME="Test Committer"
export GIT_COMMITTER_EMAIL="committer@example.com"

create_git_workspace() {
    local dir=$1; shift

    mkdir -p $dir
    pushd $dir
    git init ${1+"$@"}
    popd
}

create_git_server() {
    local dir=$1; shift

    create_git_workspace $dir --bare
    pushd $dir
    # Remove sample hooks just so it is easier to see what I've installed
    rm -f hooks/*.sample
    git-replay init-server
    popd
}

create_git_client() {
    local server=$1; shift
    local dir=$1; shift

    mkdir -p $(dirname $dir)
    git clone $server $dir
    pushd $dir
    # Remove sample hooks just so it is easier to see what I've installed
    rm -f hooks/*.sample
    git-replay init
    popd
}

quick_commit_files() {
    local msg=$1; shift

    for filename in ${1+"$@"}
    do
        touch $filename
        git add $filename
    done
    git commit -m "$msg"
}

assert_equal() {
    local name=$1; shift
    local expected=$1; shift
    local actual=$1; shift
    if [ "$expected" != "$actual" ]
    then
        echo "$name expected to be '$expected' but was $actual"
        exit 1
    fi
}

assert_not_equal() {
    local name=$1; shift
    local expected=$1; shift
    local actual=$1; shift
    if [ "$expected" = "$actual" ]
    then
        echo "$name expected to be differrent but were equal '$expected'"
        exit 1
    fi
}

# This doesn't look like much but it fails under `set -e` when the sub-command
# succeeds. The `!` operator doesn't do this on its own.
not() {
    ! ${1+"$@"}
}

TEST_TMP_DIR=$(mktemp -d)
cleanup() {
    rm -rf $TEST_TMP_DIR
}
trap cleanup EXIT
