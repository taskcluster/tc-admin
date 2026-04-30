# Making a release

The `release.sh` script is the only supported way to cut a release of
`tc-admin`. It bumps the version, builds Python distributions, publishes
to PyPI and Docker Hub, and pushes a signed tag to GitHub.

## Prerequisites

You need the following tools available on `PATH`:

| Tool | Purpose |
|------|---------|
| `git` | committing, tagging, pushing |
| `python3` | building the sdist / wheel |
| `docker` (with `buildx`) | building the multi-arch image |
| `pass` | retrieving PyPI / Docker Hub credentials |
| `gpg` | signing the git tag (`git tag -s`) |

You must also have:

- A GPG secret key — required to sign the git tag.
- An SSH key with push access to `git@github.com:taskcluster/tc-admin`.
- An entry `community-tc/secret-values.yml` in your `pass` store containing
  a `tc-admin-release-pypi-password:` line.
- An entry `hub.docker.com/taskclusterbot` in your `pass` store containing
  the Docker Hub password for the `taskclusterbot` account.
- Maintainer rights on:
  - https://pypi.org/project/tc-admin/
  - https://hub.docker.com/r/taskcluster/tc-admin
  - https://github.com/taskcluster/tc-admin

The script's pre-flight phase verifies most of the above before doing
any destructive work, and reports all problems together so you can fix
them in a single pass.

You must run the script with **no Python virtualenv active** — it builds
its own venv under `.release/py3/`.

## Running

```bash
./release.sh --version 1.2.3
```

The version must match `<a>.<b>.<c>` where `a >= 1`, `b >= 0`, `c >= 0`,
all integers, no leading zeros. An optional `alpha<n>` suffix is allowed
on the patch component.

## What the script does

1. **Pre-flight checks** — verifies tools (`git`, `python3`, `docker`,
   `pass`, `gpg`), Docker daemon and `buildx`, GPG secret key,
   `pass` entries, version-string format (old and new), branch is
   `main`, working tree is clean, local HEAD matches remote `main`,
   and that the tag does not already exist locally or remotely. All
   problems are reported together.
2. **Version bump** — updates `setup.py` and the `tc-admin~=…` line in
   `Dockerfile` via `sed` and stages the changes.
3. **Local commit + signed tag** — creates a `Version bump from X to Y`
   commit and a signed `vX.Y.Z` tag locally. Nothing is pushed yet.
4. **Build** — creates a fresh virtualenv under `.release/py3/`,
   installs `build` and `twine`, then runs `python -m build` to produce
   the sdist and wheel in `dist/`.
5. **Validate package** — `twine check dist/*` checks that the package
   metadata is valid (long_description renders cleanly on PyPI,
   classifiers are recognised, etc.) before contacting the index.
6. **Publish to PyPI** — `twine upload` to https://upload.pypi.org/legacy/.
   The PyPI password is retrieved from `pass` and printed for manual
   paste at the prompt.
7. **Publish to Docker Hub** — `docker login`, then
   `docker buildx build --platform linux/amd64,linux/arm64 --push` to
   `taskcluster/tc-admin:<version>`. The Docker Hub password is
   retrieved from `pass` and printed for manual paste.
8. **Push to GitHub** — pushes the version-bump commit to `main` and
   the signed tag. This is intentionally the last step so that a
   publish failure leaves the remote untouched.
9. **Open release page** — opens
   `https://github.com/taskcluster/tc-admin/releases/new?tag=v<version>`
   in your browser so you can write the release notes.

## Verifying before publishing

`twine check` (run automatically by the script) catches the most common
metadata problems — bad README rendering, unrecognised classifiers,
missing required fields — without contacting PyPI.

For the rare case where you want to see how the package will *render
live* on PyPI before committing to a real release (typically when
materially changing `long_description`, `long_description_content_type`,
or other metadata), you can do an end-to-end test against
[test.pypi.org](https://test.pypi.org) outside the release script:

```bash
rm -rf dist/*
python -m build
twine check dist/*
twine upload --repository testpypi dist/*
```

…then look at the result on https://test.pypi.org/project/tc-admin/.
Note that test PyPI does not allow re-uploading the same version, so
use a throwaway version (e.g. an `alpha<n>` suffix) when testing.

## Recovering from a failed run

Because the GitHub push happens at the end, a failure during build,
PyPI upload, or Docker Hub publish leaves the remote untouched. To
recover:

```bash
git reset --hard HEAD~1     # undo the version-bump commit
git tag -d "v<version>"     # remove the local signed tag
```

…then fix the underlying cause and re-run `./release.sh`.

If the failure happens *after* a successful PyPI or Docker Hub upload,
you cannot reuse the same version number — PyPI does not allow
re-uploading a version, and the Docker tag has already been published.
In that case, cut the next patch release instead.
