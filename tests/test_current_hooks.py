# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.resources import Resources, Hook
from ciadmin.current.hooks import fetch_hooks


@pytest.fixture
def Hooks(mocker):
    """
    Mock out Hooks in ciadmin.current.hooks.

    The expected list of hooks should be set in Hooks.hooks.  The set of hookGroupIds
    for which listHooks was called is in Hooks.listHookCalls.
    """
    Hooks = mocker.patch("ciadmin.current.hooks.Hooks")
    Hooks.hooks = []
    Hooks.listHookCalls = []

    class FakeHooks:
        async def listHookGroups(self):
            groups = list(sorted(set(h["hookGroupId"] for h in Hooks.hooks)))
            return {"groups": groups}

        async def listHooks(self, hookGroupId):
            Hooks.listHookCalls.append(hookGroupId)
            return {
                "hooks": [h for h in Hooks.hooks if h["hookGroupId"] == hookGroupId]
            }

    Hooks.return_value = FakeHooks()
    return Hooks


@pytest.fixture
def make_hook():
    def make_hook(**kwargs):
        kwargs.setdefault("hookGroupId", "garbage")
        kwargs.setdefault("hookId", "test-hook")
        metadata = kwargs.setdefault("metadata", {})
        metadata.setdefault("name", "test")
        metadata.setdefault("description", "descr")
        metadata.setdefault("owner", "me@me.com")
        metadata.setdefault("emailOnError", False)
        kwargs.setdefault("schedule", ["0 0 1 * * *"])
        kwargs.setdefault("task", {})
        kwargs.setdefault("triggerSchema", {})
        kwargs.setdefault("bindings", [{"exchange": "e", "routingKeyPattern": "rkp"}])
        return kwargs

    return make_hook


@pytest.mark.asyncio
async def test_fetch_hook(Hooks, make_hook):
    resources = Resources([], [".*"])
    api_hook = make_hook()
    Hooks.hooks.append(api_hook)
    await fetch_hooks(resources)
    assert list(resources) == [Hook.from_api(api_hook)]


@pytest.mark.asyncio
async def test_fetch_hook_managed_filter(Hooks, make_hook):
    "The managed resource dictate which hooks are fetched, including which groups"
    resources = Resources(
        [], ["Hook=garbage/.*", "Hook=proj.*", "Hook=imbstack/test4.*"]
    )
    hooks = [
        # managed:
        make_hook(hookGroupId="garbage", hookId="test1"),
        make_hook(hookGroupId="garbage", hookId="test2"),
        make_hook(hookGroupId="project:gecko", hookId="test3"),
        # not managed:
        make_hook(hookGroupId="imbstack", hookId="test5"),  # but imbstack is fetched
        make_hook(hookGroupId="notmanaged", hookId="test5"),
    ]
    Hooks.hooks.extend(hooks)
    await fetch_hooks(resources)
    assert list(resources) == sorted([Hook.from_api(h) for h in hooks[:3]])
    assert Hooks.listHookCalls == ["garbage", "imbstack", "project:gecko"]
