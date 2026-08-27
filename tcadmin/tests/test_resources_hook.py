# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json
import pytest
import textwrap

from tcadmin.resources.hook import Hook, Binding
from tcadmin.resources.resources import Resource


pytestmark = pytest.mark.usefixtures("appconfig")


@pytest.fixture(scope="module")
def simple_hook():
    return Hook(
        hookGroupId="garbage",
        hookId="test-hook",
        name="test",
        description="This is my hook",
        owner="me@me.com",
        emailOnError=False,
        schedule=[],
        task={"$magic": "Siri, please test my code"},
        bindings=(Binding(exchange="e", routingKeyPattern="rkp"),),
        triggerSchema={},
    )


def test_hook_id(simple_hook):
    "A hook id contains both hookGroupId and hookId"
    assert simple_hook.id == "Hook=garbage/test-hook"


def test_hook_formatter(simple_hook):
    "Hooks are properly formatted with a string"
    print(simple_hook)
    assert str(simple_hook) == textwrap.dedent(
        """\
        Hook=garbage/test-hook:
          hookGroupId: garbage
          hookId: test-hook
          name: test
          description:
            *DO NOT EDIT* - This resource is configured automatically.

            This is my hook
          owner: me@me.com
          emailOnError: False
          schedule: 
          bindings: - Binding(exchange='e', routingKeyPattern='rkp')
          task:
            {
                "$magic": "Siri, please test my code"
            }
          triggerSchema: {}"""  # noqa: E501, W291
    )


def test_hook_json_roundtrip(simple_hook):
    "A Hook survives to_json() -> json.dumps() -> json.loads() -> from_json()"
    blob = json.loads(json.dumps(simple_hook.to_json()))
    reconstructed = Resource.from_json(blob)
    assert reconstructed == simple_hook


def test_hook_bindings_rejects_dicts_not_shaped_like_binding():
    "A dict that merely happens to not match Binding's fields is rejected, not coerced"
    with pytest.raises(ValueError, match="bindings must be a sequence of Binding"):
        Hook(
            hookGroupId="g",
            hookId="h",
            name="n",
            description="d",
            owner="me@me.com",
            emailOnError=False,
            schedule=[],
            task={},
            bindings=[{"exchange": "e", "unexpectedField": "x"}],
            triggerSchema={},
        )


def test_role_from_api():
    "Hooks are properly read from a Taskcluster API result"
    api_result = {
        "hookGroupId": "garbage",
        "hookId": "test",
        "metadata": {
            "name": "my-test",
            "description": "*DO NOT EDIT* - This resource is configured automatically."
            "\n\nThis is my role",
            "owner": "dustin@mozilla.com",
            "emailOnError": False,
        },
        "schedule": ["0 0 9,21 * * 1-5", "0 0 12 * * 0,6"],
        "task": {"$magic": "build-task"},
        "triggerSchema": {},
        "bindings": [{"exchange": "e", "routingKeyPattern": "rkp"}],
    }
    hook = Hook.from_api(api_result)
    assert hook.hookGroupId == "garbage"
    assert hook.hookId == "test"
    assert hook.name == "my-test"
    assert hook.description == api_result["metadata"]["description"]
    assert hook.owner == "dustin@mozilla.com"
    assert not hook.emailOnError
    assert hook.schedule == ("0 0 9,21 * * 1-5", "0 0 12 * * 0,6")
    assert hook.task == {"$magic": "build-task"}
    assert hook.bindings == (Binding(exchange="e", routingKeyPattern="rkp"),)
    assert hook.triggerSchema == {}
