The `tc-admin` library supports administration of the runtime configuration of a Taskcluster deployment.
This means creation and maintenance of resources such as roles, hooks, and worker pools, based on version-controlled specifications..

# Usage

This library is used as a dependency of a Python application containing code and configuration specific to the taskcluster deployment(s) being administered.
The project should contain a `tc-admin.py` that serves to define the application configuration.

Assuming that is in place, the tool is easy to use:

After installing the app, run `tc-admin generate` to generate the expected set of resources (use `--json` to get JSON output).
This will require `TASKCLUSTER_ROOT_URL` to be set in the environment, to know which deployment to talk to.
Similarly, `tc-admin current` will generate the current set of resources (optionally with `--json`).
To compare them, run `tc-admin diff`.

Run `tc-admin apply` to apply the changes.
Note that only `apply` will require Taskcluster credentials, and it's a good practice to only set TC credentials when running this command.

See `tc-admin <command> --help` for more useful options.

## Checks

Checks are a way to double-check that purpose-specific invariants are satisfied in a Taskcluster deployment.
For example, it may be important to check that only specific repository roles have scopes to create tasks in critical worker pools.
Checks are defined as normal Python tests, and have access to the current and generated configurations.

If the app has checks set up, then `tc-admin check` will run those checks.

# Quick Guide to Library Operation

The operation of this tool is pretty simple: it generates a set of expected Taskcluster resources, downloads existing resources from the Taskcluster API, and compares them.
A collection of resources also specifies the set of "managed" resources -- this allows deletion of resources that are no longer expected, without risk of deleting *everything* in the Taskcluster API.

After generation, resources can be "modified".
This is typically used to make minor changes to resources depending on environment.
For exmaple, in a staging environment, hook schedules might be removed.

# App Configuration

## `tc-admin` and `tc-admin.py`

A tc-admin app is configured by `tc-admin.py`.
This is a Python file which is responsible for creating and customizing an `AppConfig` object.

```python
from tcadmin.appconfig import AppConfig

appconfig = AppConfig()
# .. customize
```

The `tc-admin` command looks for `tc-admin.py` in the current directory, or in the directory given by `$TC_ADMIN_PY` or command-line argument `--tc-admin-py`.
Like most Python modules, the global `__file__` is set when `tc-admin.py` is executed, and can be used to determine relative paths.

## Programmatic Interface

This library can also be used programmatically.
Simply create an AppConfig object directly and call `tcadmin.main.main` with it:

```python
from tcadmin.appconfig import AppConfig
from tcadmin.main import main

def boot():
    appconfig = AppConfig()
    # .. customize
    main(appconfig)

if __name__ == "__main__":
    boot()
```

## AppConfig

The AppConfig object contains a number of properties that can be customized, described below.
During execution, the current AppConfig object is available from `AppConfig.current()`.
This can be useful when generators or modifiers are defined in separate Python modules.

### Generators

Generators generate expected Taskcluster resources and defined the managed resource names.
Each generator is an async function that is given a `Resources` object and is expected to call `resources.manage` and `resources.update`.

Generators are registered with `appconfig.generators.register`, most easily with a decorator:

```python
@appconfig.generators.register
async def update_resources(resources):
    # modify in place ...
```

### Modifiers

Modifiers are responsible for modifying an existing set of reosurces.
Since resources are immutable, the signature differs slightly from generators:

```python
@appconfig.modifiers.register
async def modify_resources(resources):
    # return new set of resources
    return resources.map(..)
```

Modifiers are called sequentially in the order in which they were registered.

### Command-Line Options

Apps can add additional command-line options, the values of which are then available during resource generation.

To register an option, call `appconfig.options.add`, with the full option name and any of the following keyword options:
 * `required` - if True, the option is required
 * `help` - help string to be shown in `tc-admin generate --help`
 * `default` - default value for the option

To retrieve the option value during generation, call `appconfig.options.get(name)`.
All together, then:

```python
appconfig.options.add("--branch", help="configuration branch to read from")

@appconfig.generators.register
async def update_resources(resources):
    branch = appconfig.options.get("--branch")
    # ...
```

### Checks

The `appconfig.check_path` property gives the path of the checks to run for `tc-admin check`, relative to the current directory.
This directory is a "normal" pytest directory.

To help distinguish checks from tests, include a `pytest.ini` in this directory:

```ini
[pytest]
python_classes = Check*
python_files = check_*.py
python_functions = check_*
```

## Resources

The `tcadmin.resources` package contains clasess for defining Taskcluster resources and collections.

```python
from tcadmin.resources import Resources
```

The `Resources` class defines a collection of resources and tracks what resources are managed.
Resources found in the Taskcluster deployment that match the "managed" patterns but are not generated will be deleted on `apply`.
The class has the following methods:

* `resources.add(resource)` - add a resource to the collection.  The resource must be managed.
* `resources.update(iterable)` - add an iterable full of resources to the collection.  All resources must be managed.
* `resources.manage(pattern)` - consider reources matching regular expression string `pattern` to be managed
* `resources.filter(pattern)` - return a new Resources object containing only resources matching the given regular expression string
* `resources.map(functor)` - return a new Resources object, with fuctor applied to each resource.  This is typically used in modifiers.

The remaining classes represent individual resources.
Each has an `id` formed from its kind and the unique identifier for the resource in the Taskcluster.
For example, `Hook=release-hooks/beta-release`.
Resources are immutable once created, but can be "evolved" (returning a new resource) with `rsrc.evolve(**updates)`.

Resources with descriptions automatically prepend a "DO NOT EDIT" prefix to dissuade users from editing them in the Taskcluster UI.

### Hook

```python
from tcadmin.resources import Hook, Binding

hook = Hook(
    hookGroupId=..,
    hookId=..,
    name=..,
    description=..,
    owner=..,
    emailOnError=..,
    schedule=(.., ..),
    bindings=(.., ..),
    task={..},
    triggerSchema={..})
```

Most of these fields correspond directly to the Taskcluster definition.
Both `schedule` and `bindings` must be tuples, not lists (as lists are mutable).
The items in `schedule` are cron-like strings.
The items in `bindings` are instances of `Binding(exchange=.., routingKeyPattern=..)`.

### Role

```python
from tcadmin.resources import Role

hook = Role(
    roleId=..,
    description=..,
    scopes=(.., ..))
```

As with hooks, `scopes` must be a tuple (not a list) of strings.

### WorkerPool

```python
from tcadmin.resources import WorkerPool

hook = WorkerPool(
    workerPoolId=..,
    providerId=..,
    description=..,
    owner=..,
    config={..},
    emailOnError=..)
```

All attributes of this class match the Taskcluster definition.

## Utiliites

The library provides a number of utilities for common application requirements.

*NOTE*: only functions described in this README are considered stable.
Other functions defined by the library may change without notice.

### Scopes

As an aid to writing checks, tc-admin supplies local implementations of various scope-related algorithms.

```python
from tcadmin.util.scopes import satisfies, normalizeScopes, Resolver
```

The `satisfies` function determines scope satisfaction, without any expansion.
Satisfaction means that the first argument contains all scopes in the second argument.

```python
assert satisfies(['balloons:*', 'cake:birthday'], ['baloons:mylar:happy-birthday'])
```

The `normalizeScopes` function normalizes a scopeset, removing redundant scopes and sorting.

```python
assert normalizedScopes(['balloons:*', 'balloons:mylar:*']) == ['baloons:*']
```

Finally, `Resolver` can perform scope expansion.
It is initialized with a dictionary mapping roleIds to scope lists.
Alternately, it can be initialized from a `Resources` instance using `Resolver.from_resources(resources)`.

Its `expandScopes` method behaves identically to the remote call `auth.expandScopes`.

```python
resolver = Resolver.from_resources(resources)
assert resolver.expandScopes(['assume:clown:grimaldi']) == ['assume:clown:grimaldi', 'ruffle:full']
```

### aiohttp session

The library uses `aiohttp` to communicate with Taskcluster, and establishes a single session for efficiency.
Applications can use the same session for any other HTTP operations.

```python
from tcadmin.util.session import aiohttp_session

async def foo():
    # ...
    async with aiohttp_session().get(url) as response:
        response.raise_for_status()
        result = await response.read()
```

Tests and checks can set this value using `with_aiohttp_session`:

```python
from tcadmin.util.sessions import with_aiohttp_session
import pytest

@pytest.mark.asyncio
@with_aiohttp_session
async def test_something():
    # ...
```

### MatchList

A MatchList is a list of regular expressions that can determine whether a given
string matches one of those patterns.  Patterns are rooted at the left, but
should use `$` where required to match the end of the string.

```python
from tcadmin.util.matchlist import MatchList

ml = MatchList()
ml.add("fo+$")
ml.add("ba+r$")
assert ml.matches("foo")
```

This functionality is used to track managed resources, but may be useful otherwise.

### Root URL

The current root_url is available from a short helper function:

```python
from tcadmin.util.root_url import root_url

print(root_url())
```

This does little more than retrieve the value from `os.environ`, but is a little less verbose.

# Development

To install for development, in a virtualenv:

```
pip install -e [path]
```

And to run flake8 and tests:

```
python setup.py flake8
python setup.py test
```

The library uses [Black](https://black.readthedocs.io/en/stable/) to format code.

```
pip install black
black tcadmin
```
