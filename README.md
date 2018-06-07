**Manage runtime configuration for Firefox CI**

# Usage

After installing, run `ci-admin generate` to generate the expected CI configuration (use `--json` to get JSON output)
Similarly, `ci-admin current` will generate the current CI configuration (optionally with `--json`).
To compare them, run `ci-admin diff`.
Run `ci-admin apply` to apply the changes.
Note that the latter will require Taskcluster credentials.

# Quick Guide

The operation of this tool is pretty simple: it generates a set of expected Taskcluster resources (roles, hooks, etc.), downloads existing resources from the Taskcluster API, and compares them.
A collection of resources also specifies the set of "managed" resources -- this allows deletion of resources that are no longer expected, without risk of deleting *everything* in the Taskcluster API.

If you are looking to modify the expected resources, look in `ciadmin/generate`.
Generation is divided by theme into several Python files there.
Comments and docstrings should guide you from that point.

To test your changes, use `ci-admin diff`.
You do not need any Taskcluster credentials to run this command, and it's best that none are configured in your shell -- to avoid accidents.

If you need to make modifications to the `ci-configuration` repository, you can point these tools to a local copy of the repository with `--ci-configuration-directory`.
You can also point to a different repository or revision with `--ci-configuration-repository` and `--ci-configuration-revision`, respectively.


# Development

To install for development, in a virtualenv:

```
pip install -e
```

And to run flake8 and tests:

```
python setup.py flake8
python setup.py test
```
