# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

"""
Tests for ``Resource.from_api``: live-API descriptions are preserved
verbatim (the ``*DO NOT EDIT*`` prefix is not injected); the ordering/type
converters for scopes, bindings, and schedule continue to run on both the
constructor and ``from_api`` paths.
"""

import pytest

from tcadmin.resources.client import Client
from tcadmin.resources.role import Role
from tcadmin.resources.hook import Hook, Binding
from tcadmin.resources.worker_pool import WorkerPool
from tcadmin.resources.secret import Secret


pytestmark = pytest.mark.usefixtures("appconfig")


# --- Client ------------------------------------------------------------------

def test_client_from_api_preserves_raw_description():
    "from_api preserves the API description as-is, without prepending a prefix"
    api_result = {
        "clientId": "cid",
        "description": "raw description without prefix",
        "scopes": ["scope-a"],
    }
    client = Client.from_api(api_result)
    assert client.description == "raw description without prefix"


def test_client_from_api_preserves_empty_description():
    "from_api preserves an empty API description as empty (does not inject prefix)"
    api_result = {
        "clientId": "cid",
        "description": "",
        "scopes": [],
    }
    client = Client.from_api(api_result)
    assert client.description == ""


def test_client_from_api_sorts_scopes():
    "from_api still applies scopes_converter (sort + tuple)"
    api_result = {
        "clientId": "cid",
        "description": "*DO NOT EDIT* - desc",
        "scopes": ["c", "a", "b"],
    }
    client = Client.from_api(api_result)
    assert client.scopes == ("a", "b", "c")
    assert isinstance(client.scopes, tuple)


def test_client_constructor_still_runs_converters():
    "Constructing a Client directly (e.g. from YAML) still runs converters"
    client = Client(clientId="cid", description="user-supplied", scopes=["c", "a"])
    assert client.description.startswith("*DO NOT EDIT*")
    assert client.description.endswith("user-supplied")
    assert client.scopes == ("a", "c")


# --- Role --------------------------------------------------------------------

def test_role_from_api_preserves_raw_description():
    api_result = {
        "roleId": "rid",
        "description": "raw description without prefix",
        "scopes": ["scope-a"],
    }
    role = Role.from_api(api_result)
    assert role.description == "raw description without prefix"


def test_role_from_api_sorts_scopes():
    api_result = {
        "roleId": "rid",
        "description": "*DO NOT EDIT* - desc",
        "scopes": ["z", "a", "m"],
    }
    role = Role.from_api(api_result)
    assert role.scopes == ("a", "m", "z")
    assert isinstance(role.scopes, tuple)


def test_role_constructor_still_runs_converters():
    role = Role(roleId="rid", description="user-supplied", scopes=["c", "a"])
    assert role.description.startswith("*DO NOT EDIT*")
    assert role.description.endswith("user-supplied")
    assert role.scopes == ("a", "c")


# --- Hook --------------------------------------------------------------------

def _hook_api_result(**overrides):
    base = {
        "hookGroupId": "g",
        "hookId": "h",
        "metadata": {
            "name": "n",
            "description": "raw description without prefix",
            "owner": "o@e.com",
            "emailOnError": False,
        },
        "schedule": ["0 0 * * * *"],
        "task": {"$magic": "task"},
        "triggerSchema": {},
        "bindings": [
            {"exchange": "z-exchange", "routingKeyPattern": "rkp"},
            {"exchange": "a-exchange", "routingKeyPattern": "rkp"},
        ],
    }
    base.update(overrides)
    return base


def test_hook_from_api_preserves_raw_description():
    hook = Hook.from_api(_hook_api_result())
    assert hook.description == "raw description without prefix"


def test_hook_from_api_sorts_bindings():
    "from_api still applies bindings_converter (sort + tuple)"
    hook = Hook.from_api(_hook_api_result())
    assert hook.bindings == (
        Binding(exchange="a-exchange", routingKeyPattern="rkp"),
        Binding(exchange="z-exchange", routingKeyPattern="rkp"),
    )
    assert isinstance(hook.bindings, tuple)


def test_hook_from_api_schedule_is_tuple():
    "from_api still applies schedule_converter (list → tuple)"
    hook = Hook.from_api(_hook_api_result())
    assert isinstance(hook.schedule, tuple)
    assert hook.schedule == ("0 0 * * * *",)


def test_hook_constructor_still_runs_converters():
    "Constructing a Hook directly still applies description prefix and sorts bindings"
    hook = Hook(
        hookGroupId="g",
        hookId="h",
        name="n",
        description="user-supplied",
        owner="o@e.com",
        emailOnError=False,
        schedule=["0 0 * * * *"],
        bindings=[
            Binding(exchange="z", routingKeyPattern="rkp"),
            Binding(exchange="a", routingKeyPattern="rkp"),
        ],
        task={},
        triggerSchema={},
    )
    assert hook.description.startswith("*DO NOT EDIT*")
    assert hook.description.endswith("user-supplied")
    assert hook.bindings[0].exchange == "a"
    assert hook.bindings[1].exchange == "z"
    assert isinstance(hook.schedule, tuple)


# --- WorkerPool --------------------------------------------------------------

def test_worker_pool_from_api_preserves_raw_description():
    api_result = {
        "config": {"is": "config"},
        "workerPoolId": "p/w",
        "description": "raw description without prefix",
        "owner": "o@e.com",
        "emailOnError": False,
        "providerId": "static",
    }
    wp = WorkerPool.from_api(api_result)
    assert wp.description == "raw description without prefix"


def test_worker_pool_constructor_still_runs_converters():
    wp = WorkerPool(
        workerPoolId="p/w",
        description="user-supplied",
        owner="o@e.com",
        config={},
        emailOnError=False,
        providerId="static",
    )
    assert wp.description.startswith("*DO NOT EDIT*")
    assert wp.description.endswith("user-supplied")


# --- Secret (no field-level converters; verify behaviour unchanged) ---------

def test_secret_from_api_unchanged():
    api_result = {"secret": {"k": "v"}}
    secret = Secret.from_api("my-secret", api_result)
    assert secret.name == "my-secret"
    assert secret.secret == {"k": "v"}
