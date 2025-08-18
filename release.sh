#!/usr/bin/env bash

# This script is used to generate releases of tc-admin. It should be the only
# way that releases are created. There are two phases, the first is checking
# that the code is in a clean and working state. The second phase is modifying
# files, tagging, commiting and pushing to github.

# exit in case of bad exit code or undefined var
set -eu
set -o pipefail

function usage()
{
    echo "Usage: $0 [ <option> ... ]"
    echo "Generates and publishes a release of tc-admin to pypi.org, github.com and hub.docker.com."
    echo
    echo "Options:"
    echo "  -v|--version <version>     Version number for release, e.g. --version 1.2.3"
	echo "  --real, -r                 Publish to https://upload.pypi.org/legacy/ (otherwise publishes to https://test.pypi.org/legacy/)"
    echo "  -h, --help                 Show this usage message"
}

function inline_sed {
    tempfile="$(mktemp -t inline_sed.XXXXXX)"
    local file="${1}"
    local exp="${2}"
    cat "${file}" | sed "${2}" > "${tempfile}"
    cat "${tempfile}" > "${file}"
    rm "${tempfile}"
    git add "${file}"
}

if [ -n "${VIRTUAL_ENV}" ]; then
    echo "Deactivate your virtualenv first" >&2
    exit 1
fi

REPOSITORY_URL='https://test.pypi.org/legacy/'
OFFICIAL_GIT_REPO='git@github.com:taskcluster/tc-admin'

# step into directory containing this script
cd "$(dirname "${0}")"

while [ ${#} -gt 0 ]; do
    case "$1" in
        -r|--real) REPOSITORY_URL='https://upload.pypi.org/legacy/'; SHIFT=1;;
        -v|--version) NEW_VERSION="$2"; SHIFT=2;;
        -h|--help) usage ; exit 0;;
        *) echo "Unknown argument: '$1'" >&2; usage >&2; exit 1;;
    esac
    if [ "${#}" -lt "${SHIFT}" ]; then
        echo "'$1' requires an argument" >&2
        usage >&2
        exit 1
    fi
    shift "${SHIFT}"
done

if [ -z "${NEW_VERSION}" ]; then
    usage >&2
    exit 64
fi

OLD_VERSION="$(cat setup.py | sed -n 's/.*version *= *"\(.*\)".*/\1/p')"

VALID_FORMAT='^[1-9][0-9]*\.\(0\|[1-9][0-9]*\)\.\(0\|[1-9]\)\([0-9]*alpha[1-9][0-9]*\|[0-9]*\)$'
FORMAT_EXPLANATION='should be "<a>.<b>.<c>" where a>=1, b>=0, c>=0 and a,b,c are integers, with no leading zeros'

if ! echo "${OLD_VERSION}" | grep -q "${VALID_FORMAT}"; then
    echo "Previous release version '${OLD_VERSION}' not allowed (${FORMAT_EXPLANATION}) - please fix setup.py" >&2
    exit 65
fi

if ! echo "${NEW_VERSION}" | grep -q "${VALID_FORMAT}"; then
    echo "Release version '${NEW_VERSION}' not allowed (${FORMAT_EXPLANATION})" >&2
    exit 66
fi

echo "Previous release: ${OLD_VERSION}"
echo "New release:      ${NEW_VERSION}"

if [ "${OLD_VERSION}" == "${NEW_VERSION}" ]; then
    echo "Cannot release since release version specified is the same as the current release number" >&2
    exit 67
fi

# Make sure git tag doesn't already exist on remote
if [ "$(git ls-remote -t "${OFFICIAL_GIT_REPO}" "v${NEW_VERSION}" 2>&1 | wc -l | tr -d ' ')" != '0' ]; then
    echo "git tag '${NEW_VERSION}' already exists remotely on ${OFFICIAL_GIT_REPO},"
    echo "or there was an error checking whether it existed:"
    git ls-remote -t "${OFFICIAL_GIT_REPO}" "v${NEW_VERSION}"
    exit 68
fi

# Local changes will not be in the release, so they should be dealt with before
# continuing. git stash can help here! Untracked files can make it into release
# so let's make sure we have none of them either.
modified="$(git status --porcelain)"
if [ -n "$modified" ]; then
    echo "There are changes in the local tree. This probably means"
    echo "you'll do something unintentional. For safety's sake, please"
    echo 'revert or stash them!'
    echo
    git status
    exit 69
fi

remoteMasterSha="$(git ls-remote "${OFFICIAL_GIT_REPO}" main | cut -f1)"
localSha="$(git rev-parse HEAD)"
if [ "${remoteMasterSha}" != "${localSha}" ]; then
    echo "Locally, you are on commit ${localSha}."
    echo "The remote taskcluster repo main branch is on commit ${remoteMasterSha}."
    echo "Make sure to git push/pull so that they both point to the same commit."
    exit 70
fi

inline_sed setup.py "s/\(version *= *\)\"${OLD_VERSION//./\\.}\"/\\1\"${NEW_VERSION}\"/"
inline_sed Dockerfile "s/\(tc-admin *~= *\)${OLD_VERSION//./\\.}/\\1${NEW_VERSION}/"

git commit -m "Version bump from ${OLD_VERSION} to ${NEW_VERSION}"
git tag -s "v${NEW_VERSION}" -m "Making release ${NEW_VERSION}"
git push "${OFFICIAL_GIT_REPO}" "+HEAD:refs/heads/main"
git fetch --all
git push "${OFFICIAL_GIT_REPO}" "+refs/tags/v${NEW_VERSION}:refs/tags/v${NEW_VERSION}"

# begin making the distribution
rm -f dist/*
rm -rf .release
mkdir -p .release

python3 -mvenv .release/py3
.release/py3/bin/pip install -U pip
.release/py3/bin/pip install -U setuptools twine wheel
.release/py3/bin/python setup.py sdist
.release/py3/bin/python setup.py bdist_wheel

# Work around https://bitbucket.org/pypa/wheel/issues/147/bdist_wheel-should-start-by-cleaning-up
rm -rf build/

ls -al dist

pass git pull

echo
echo
echo '******** USE THIS WHEN PROMPTED! ********'
echo
echo
pass community-tc/secret-values.yml | sed -n 's/tc-admin-release-pypi-password: *//p'
echo
echo
echo


# Publish to PyPI using Twine, as recommended by:
# https://packaging.python.org/tutorials/distributing-packages/#uploading-your-project-to-pypi
.release/py3/bin/twine upload --repository-url $REPOSITORY_URL dist/*

echo
echo
echo '******** USE THIS WHEN PROMPTED! ********'
echo
echo
pass hub.docker.com/taskclusterbot   # fetch credentials for making docker release
echo
echo
echo
docker logout
docker login
docker build -t "taskcluster/tc-admin:${NEW_VERSION}" .
docker push "taskcluster/tc-admin:${NEW_VERSION}"
echo
echo "Now go to https://github.com/taskcluster/tc-admin/releases/new?tag=v${NEW_VERSION} and create a new release with a description of the changes"
