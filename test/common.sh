export GIT_AUTHOR_NAME="Test Author"
export GIT_AUTHOR_EMAIL="author@example.com"
export GIT_COMMITTER_NAME="Test Committer"
export GIT_COMMITTER_EMAIL="committer@example.com"

create_git_workspace() {
    dir=$1; shift

    mkdir -p $dir
    pushd $dir
    git init ${1+"$@"}
    popd
}

quick_commit_files() {
    msg=$1; shift

    for filename in ${1+"$@"}
    do
        touch $filename
        git add $filename
    done
    git commit -m "$msg"
}

assert_equal() {
    name=$1; shift
    expected=$1; shift
    actual=$1; shift
    if [ "$expected" != "$actual" ]
    then
        echo "$name expected to be '$expected' but was $actual"
        exit 1
    fi
}

assert_not_equal() {
    name=$1; shift
    expected=$1; shift
    actual=$1; shift
    if [ "$expected" = "$actual" ]
    then
        echo "$name expected to be differrent but were equal '$expected'"
        exit 1
    fi
}

TEST_TMP_DIR=$(mktemp -d)
cleanup() {
    rm -rf $TEST_TMP_DIR
}
trap cleanup EXIT
