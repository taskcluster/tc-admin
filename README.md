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

If the configuration includes secrets, you may want to pass the `--without-secrets` option.
This option skips managing the content of secrets, and thus needs neither access to secret values nor Taskcluster credentials to fetch secrets.

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

Before `tc-admin.py` is executed, the current working directory is changed to the directory containing it.
This enables relative imports as well as loading files with relative paths (such as with LocalLoader, below).

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

Note that the current directory is not automatically set in this case.

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

When generating secrets, respect the `--with-secrets` option, and generate secrets without values when it is false.
You can also use this option to determine whether the generation process requires access to secret values.
This allows generation runs with `--without-secrets` to occur without any credentials or access to secret values.

```python
@appconfig.generators.register
async def update_resources(resources):
    # modify in place ...
    if appconfig.options.get('--with-secrets'):
        secretstore = load_secret_values()
        resources.add(Secret(
            name="top-secret/cookie-recipe",
            secret=secretstore.decrypt('recipes/double-chocolate-chip')))
     else:
        resources.add(Secret(name="top-secret/cookie-recipe"))
```

### Modifiers

Modifiers are responsible for modifying an existing set of resources.
Since resources are immutable, the signature differs slightly from generators:

```python
@appconfig.modifiers.register
async def modify_resources(resources):
    # return new set of resources
    return resources.map(..)
```

Modifiers are called sequentially in the order in which they were registered.

### Callbacks

Callbacks are external function from your own application that can be executed at specific times during the `tc-admin apply` execution:

* A `before_apply` callback will run before a resource is created, updated or deleted,
* A `after_apply` callback will run after a resource has beencreated, updated or deleted.

Supported actions are :

* create
* update
* delete

By default all actions are used.

All resources are supported by callbacks, and enabled by default. If you want to limit your callback to some resources, you need to specify them using their class (not a string).

You can declare your callbacks as:

```python
from tcadmin.resources import Secret

async def my_action(action, resource):
    print("Got a callback on", action, resource)

# Will call your function when a secret has been updated or deleted
appconfig.callbacks.add("after_apply", my_action, actions=["update", "delete"], resources=[Secret, ])
```

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

As a special case, the `--with-secrets` secret is available through this same mechanism.

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

### description_prefix

The `appconfig.description_prefix` property allows the users to customize the prefix of the description.
This can be customized in the `tc-admin.py` as follows:

```python
from tcadmin.appconfig import AppConfig

appconfig = AppConfig()
appconfig.description_prefix = "YOUR_CUSTOM_PREFIX"
```

The DEFAULT value of the description_prefix is `*DO NOT EDIT* - This resource is configured automatically.\n\n`

### Root URL

For the common case of a configuration that applies to only one Taskcluster deployment, specify that deployment's root URL in `tc-admin.py`:

```python
from tcadmin.appconfig import AppConfig

appconfig = AppConfig()
appconfig.root_url = "https://taskcluster.example.com"
```

To support more complex cases, this value can also be an async callable.
It will be invoked once, after the `click` options have been processed, so it can access `appconfig.options` if necessary.

The current root URL is available from an async helper function:

```python
from tcadmin.util.root_url import root_url

async def foo():
    print(await root_url())
```

This will retrieve the value from the AppConfig or, if that is not set, from `TASKCLUSTER_ROOT_URL`.
If both are set, and the values do not match, it will produce an error message.

### Loading Config Sources

Most uses of this library load configuration data from some easily-modified YAML files.
The `tcadmin.util.config` package provides some support for loading and parsing these files.
All of this is entirely optional; use what is appropriate to the purpose.

#### Loaders

First, define a loader that can load data from files.

```python
from tcadmin.util.config import LocalLoader

loader = LocalLoader()
```

The LocalLoader class knows how to load configuration from files relative to `tc-admin.py`.
It has a `load` method that will load data, optionally parsing it as YAML:

```python
data = loader.load("data.bin")
aliases = await loader.load("aliases.yml", parse="yaml")
```

You can also define your own loader class.
Just implement the `load_raw` method to return bytes, given a filename.

#### Config

YAML data is inconvenient to deal with in Python, introducig a lot of `[".."]` noise.
Commonly, config files are either a top-level array, or a top-level object with named "stanzas" of configuration.
The ConfigList and ConfigDict classes support these formats.
We suggest using these with the Python `attrs` library.

Define a class that inherits from either of these classes, specifies the filename to load from, and has an `Item` class for the items in the collection:

```python
from tcadmin.util.config import ConfigList

class Workers(ConfigList):
    filename = "workers.yml"

    @attr.s
    class Item:
        workerId = attr.ib(type=str)
        bigness = attr.ib(type=int, default=1)
```

Then simply call `await Workers.load(loader)` to load a `workers.yml` that looks something like

```yaml
- workerId: small
  bigness: 5
- workerId: huge
  bigness: 5000
```

The ConfigDict class is similar, but parses files like

```yaml
small:
  bigness: 5
huge:
  bigness: 5000
```

ConfigList creates new `Item` instances from array elements `item` with `Item(**item)`.
ConfigDict creates new `Item` instances from `k: item` with `Item(k, **item)`.
This approach is compatible with `attrs`, where in the latter case `k` should be the first attribute defined.

If array elements or object values are not themselves YAML objects, add a class method named `transform_item` to transform the data in the YAML file into a Python dictionary.
For example:

```python
class Workers(ConfigList):

    @classmethod
    def transform_item(cls, item):
        # given a simple string, assume that is the workerId and apply defaults
        if isinstance(item, str):
            return {"workerId": item}
        return item

    ...
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
* `resources.is_managed(id)` - return true if the given resource is managed
* `resources.filter(pattern)` - return a new Resources object containing only resources matching the given regular expression string
* `resources.map(functor)` - return a new Resources object, with fuctor applied to each resource.  This is typically used in modifiers.

Resources must be unique -- tc-admin cannot manage multiple hooks with the same name, for example.
However, some resource kinds support merging, where adding a resource with the same identity as one that already exists "merges" it into the existing resource.
See the description of roles, below.

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

### Secret

```python
from tcadmin.resources import Secret

secret = Secret(
    name=..,
    secret=..)

# or, when not managing secret values

secret = Secret(name=..)
```

Secrets are managed using the Secret resource type.
While Taskcluster supports expiration times on secrets, this library sets those times the far future, effectively creating non-expiring secrets

This library is careful to not display secret values in its output.
Instead, it displays `<unknown>` when not managing secret values, and displays a salted hash of the secret value when managing secret values.
The salted hash allows `tc-admin diff` to show that a secret value has changed, without revealing the value of that secret.
The salt includes a per-run salt, and the name of the secret, with the result that even if two secrets have the same value, they will be shown with different hashes in `tc-admin generate`.

### Role

```python
from tcadmin.resources import Role

role = Role(
    roleId=..,
    description=..,
    scopes=(.., ..))
```

As with hooks, `scopes` must be a tuple (not a list) of strings.

Roles can be merged if their descriptions match.
The resulting role contains the union of the scopes of the input roles.
This functionality makes management of roles easier in cases where different parts of the generation process may add scopes to the same role.

For example:

```python
resources.add(Role(roleId="my-role", description="My Role", scopes=["scope1"]))
resources.add(Role(roleId="my-role", description="My Role", scopes=["scope2"]))
```

This will result in a single Role with scopes `["scope1", "scope2"]`.

### Client

```python
from tcadmin.resources import Client

client = Client(
    clientId=..,
    description=..,
    scopes=(.., ..))
```

Clients work much like roles.
As with roles, `scopes` must be a tuple (not a list) of strings.
This library does not manage access tokens: it discards them from the response to `auth.createClient`.
The expectation is that project admins who need credentials for the managed clients will call `auth.resetAccessToken` and use the returned token.

Clients configured by this library have an expiration date far in the future.
Like roles, the clients managed here last "forever".

### WorkerPool

```python
from tcadmin.resources import WorkerPool

workerPool = WorkerPool(
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

## Releasing

To release:

 * update version in `setup.py` and `git commit -m "vX.Y.Z"`
 * `git tag vX.Y.Z`
 * `git push`
 * `git push --tags`
 * `./release.sh --real` and enter your pypi credentials when prompted (omit the `--real` to try it against the testing pypi, if you're not sure)
 * go to https://github.com/taskcluster/tc-admin/releases/tag/vX.Y.Z and create a new release from the tag with a brief description of the changes
 * build and publish a new version of the linux/amd64 tc-admin docker image:

```bash
pass git pull
pass hub.docker.com/taskclusterbot   # fetch credentials for making docker release
docker logout
docker login                         # use credentials output above
docker build -t taskcluster/tc-admin:X.Y.Z .
docker push taskcluster/tc-admin:X.Y.Z
```
