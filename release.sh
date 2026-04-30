#!/usr/bin/env bash

# This script is used to generate releases of tc-admin. It should be the only
# way that releases are created.
#
# Phase 1 (preflight): verify the environment, credentials and repository
#   state. All problems are collected and reported together so they can be
#   fixed in a single pass.
#
# Phase 2 (release): bump the version, build, publish to PyPI and Docker Hub,
#   and finally push the commit and signed tag to GitHub.
#
# The git push to GitHub happens AFTER the PyPI and Docker Hub publishes
# succeed, so a publish failure leaves the remote untouched. To recover
# from a failed run:
#
#   git reset --hard HEAD~1     # undo the version-bump commit
#   git tag -d "v<version>"     # remove the local tag
#
# ...then fix the underlying problem and re-run.

# exit in case of bad exit code or undefined var
set -eu
set -o pipefail

PYPI_URL='https://upload.pypi.org/legacy/'
OFFICIAL_GIT_REPO='git@github.com:taskcluster/tc-admin'

VALID_FORMAT='^[1-9][0-9]*\.\(0\|[1-9][0-9]*\)\.\(0\|[1-9]\)\([0-9]*alpha[1-9][0-9]*\|[0-9]*\)$'
FORMAT_EXPLANATION='should be "<a>.<b>.<c>" where a>=1, b>=0, c>=0 and a,b,c are integers, with no leading zeros'

function usage()
{
    echo "Usage: $0 [ <option> ... ]"
    echo "Generates and publishes a release of tc-admin to pypi.org, github.com and hub.docker.com."
    echo
    echo "Options:"
    echo "  -v|--version <version>     Version number for release, e.g. --version 1.2.3"
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

function open_url {
  local url="$1"
  if [ -n "${BROWSER:-}" ]; then
    "$BROWSER" "$url" >/dev/null 2>&1 &
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v gio >/dev/null 2>&1; then
    gio open "$url" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then        # macOS
    open "$url" >/dev/null 2>&1 &
  elif command -v wslview >/dev/null 2>&1; then      # WSL
    wslview "$url" >/dev/null 2>&1 &
  elif command -v sensible-browser >/dev/null 2>&1; then  # Debian/Ubuntu
    sensible-browser "$url" >/dev/null 2>&1 &
  else
    echo 'No opener found. Install xdg-utils or set $BROWSER.' >&2
    return 1
  fi
}

# step into directory containing this script
cd "$(dirname "${0}")"

# Parse arguments
while [ ${#} -gt 0 ]; do
    case "$1" in
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

if [ -z "${NEW_VERSION:-}" ]; then
    usage >&2
    exit 64
fi

OLD_VERSION="$(cat setup.py | sed -n 's/.*version *= *"\(.*\)".*/\1/p')"

###########################################################################
# Pre-flight checks — collect all errors and report them together.
###########################################################################
function preflight()
{
    local errors=()

    echo "=== Pre-flight checks ==="

    # Not running inside a virtualenv (we build our own under .release/py3)
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        errors+=("Deactivate your virtualenv first (currently active: ${VIRTUAL_ENV})")
    fi

    # Required binaries
    for bin in git python3 docker pass gpg; do
        if ! command -v "$bin" >/dev/null 2>&1; then
            errors+=("Missing binary: $bin")
        fi
    done

    # Docker daemon reachable + buildx available
    if command -v docker >/dev/null 2>&1; then
        if ! docker info >/dev/null 2>&1; then
            errors+=("Docker daemon not reachable (is Docker running?)")
        fi
        if ! docker buildx version >/dev/null 2>&1; then
            errors+=("docker buildx not available (required for multi-arch image build)")
        fi
    fi

    # GPG secret key available (required for signed tag — git tag -s)
    if command -v gpg >/dev/null 2>&1; then
        if ! gpg --list-secret-keys 2>/dev/null | grep -q .; then
            errors+=("No GPG secret keys found (required to sign the git tag)")
        fi
    fi

    # Pass entries (sync first so we're checking the latest state)
    if command -v pass >/dev/null 2>&1; then
        pass git pull >/dev/null 2>&1 || true
        if ! pass show community-tc/secret-values.yml >/dev/null 2>&1; then
            errors+=("pass entry 'community-tc/secret-values.yml' not found (needed for PyPI password)")
        elif ! pass show community-tc/secret-values.yml | grep -q '^tc-admin-release-pypi-password:'; then
            errors+=("pass entry 'community-tc/secret-values.yml' does not contain a 'tc-admin-release-pypi-password' line")
        fi
        if ! pass show hub.docker.com/taskclusterbot >/dev/null 2>&1; then
            errors+=("pass entry 'hub.docker.com/taskclusterbot' not found (needed for Docker Hub login)")
        fi
    fi

    # Version format validation (both old and new)
    if ! echo "${OLD_VERSION}" | grep -q "${VALID_FORMAT}"; then
        errors+=("Previous release version '${OLD_VERSION}' not allowed (${FORMAT_EXPLANATION}) — please fix setup.py")
    fi
    if ! echo "${NEW_VERSION}" | grep -q "${VALID_FORMAT}"; then
        errors+=("Release version '${NEW_VERSION}' not allowed (${FORMAT_EXPLANATION})")
    fi
    if [ "${OLD_VERSION}" == "${NEW_VERSION}" ]; then
        errors+=("Cannot release: new version (${NEW_VERSION}) is the same as the current version")
    fi

    # On main branch (a SHA-only check would pass on a feature branch sitting
    # at the same commit as main, hence the explicit branch-name check).
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
    if [ "$branch" != "main" ]; then
        errors+=("Not on main branch (currently on '$branch'). To fix: git checkout main")
    fi

    # Working tree clean
    if [ -n "$(git status --porcelain)" ]; then
        errors+=("Working tree is not clean — see details below")
    fi

    # Local HEAD matches remote main (and remote is reachable)
    local remoteMasterSha localSha
    remoteMasterSha="$(git ls-remote "${OFFICIAL_GIT_REPO}" main 2>/dev/null | cut -f1)"
    if [ -z "${remoteMasterSha}" ]; then
        errors+=("Cannot reach remote ${OFFICIAL_GIT_REPO} (check SSH keys / network)")
    else
        localSha="$(git rev-parse HEAD)"
        if [ "${remoteMasterSha}" != "${localSha}" ]; then
            errors+=("Local HEAD (${localSha}) does not match remote main (${remoteMasterSha}); run git pull/push first")
        fi

        # Tag doesn't already exist on remote (only checkable when remote reachable)
        if [ "$(git ls-remote -t "${OFFICIAL_GIT_REPO}" "v${NEW_VERSION}" 2>/dev/null | wc -l | tr -d ' ')" != '0' ]; then
            errors+=("git tag v${NEW_VERSION} already exists on ${OFFICIAL_GIT_REPO}")
        fi
    fi

    # Tag doesn't already exist locally
    if git rev-parse "v${NEW_VERSION}" >/dev/null 2>&1; then
        errors+=("git tag v${NEW_VERSION} already exists locally")
    fi

    # Report
    if [ ${#errors[@]} -gt 0 ]; then
        echo
        echo "Pre-flight FAILED with ${#errors[@]} error(s):"
        for err in "${errors[@]}"; do
            echo "  - $err"
        done
        if [ -n "$(git status --porcelain)" ]; then
            echo
            echo "Working tree status:"
            git status --short
            echo
            echo "To inspect changes before discarding:"
            echo "  git diff                   # staged and unstaged changes to tracked files"
            echo "  git diff --cached          # staged changes only"
            echo "  git status                 # full status including untracked files"
            echo
            echo "To discard ALL local changes (WARNING: this is irreversible):"
            echo "  git reset --hard HEAD      # discard all changes to tracked files"
            echo "  git clean -fd              # delete untracked files and directories"
        fi
        echo
        exit 1
    fi

    echo "  All pre-flight checks passed."
    echo
}

preflight

echo "Previous release: ${OLD_VERSION}"
echo "New release:      ${NEW_VERSION}"
echo

###########################################################################
# Phase 2 — version bump, build, publish, then push to GitHub.
###########################################################################

# Bump versions in setup.py and Dockerfile
inline_sed setup.py "s/\(version *= *\)\"${OLD_VERSION//./\\.}\"/\\1\"${NEW_VERSION}\"/"
inline_sed Dockerfile "s/\(tc-admin *~= *\)${OLD_VERSION//./\\.}/\\1${NEW_VERSION}/"

# Local commit and signed tag (NOT yet pushed — push happens after publishes succeed)
git commit -m "Version bump from ${OLD_VERSION} to ${NEW_VERSION}"
git tag -s "v${NEW_VERSION}" -m "Making release ${NEW_VERSION}"

# Build sdist + wheel using the modern PEP-517 frontend
rm -f dist/*
rm -rf .release
mkdir -p .release

python3 -mvenv .release/py3
.release/py3/bin/pip install -U pip
.release/py3/bin/pip install -U build twine
.release/py3/bin/python -m build

ls -al dist

# Validate package metadata (long_description renders, classifiers valid, etc.)
# before contacting PyPI.
.release/py3/bin/twine check dist/*

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
.release/py3/bin/twine upload --repository-url $PYPI_URL dist/*

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
docker buildx create --name tc-admin-builder --use 2>/dev/null || docker buildx use tc-admin-builder
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "taskcluster/tc-admin:${NEW_VERSION}" \
  --push .

# Publishes succeeded — now push the commit and signed tag to GitHub.
git push "${OFFICIAL_GIT_REPO}" "+HEAD:refs/heads/main"
git fetch --all
git push "${OFFICIAL_GIT_REPO}" "+refs/tags/v${NEW_VERSION}:refs/tags/v${NEW_VERSION}"

echo
open_url "https://github.com/taskcluster/tc-admin/releases/new?tag=v${NEW_VERSION}"
