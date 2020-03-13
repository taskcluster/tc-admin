# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from mock import AsyncMock

from tcadmin.callbacks import CallbacksRegistry
from tcadmin.resources import Role, Hook, WorkerPool, Client, Secret


def test_registry_add():

    # Empty registry
    reg = CallbacksRegistry()
    assert reg.callbacks == {
        "before_apply": [],
        "after_apply": [],
    }

    # Add a dummy callback
    callback = reg.add("before_apply", lambda: True)
    assert callback.actions == ["create", "update", "delete"]
    assert callback.resources == (Role, Hook, WorkerPool, Client, Secret)
    assert callback.callable() is True
    assert len(reg.callbacks["before_apply"]) == 1

    # Invalid trigger should raise
    with pytest.raises(AssertionError, match="wontWork is not a supported trigger"):
        reg.add("wontWork", lambda: True)

    # Invalid actions should raise
    with pytest.raises(AssertionError, match="Some actions are not supported"):
        reg.add("after_apply", lambda: True, actions=["willfail", "update"])

    # Invalid resources should raise
    with pytest.raises(AssertionError, match="Some resources are not supported"):
        reg.add("after_apply", lambda: True, resources=[Role, "fail"])


@pytest.mark.asyncio
async def test_registry_run():

    reg = CallbacksRegistry()

    # Simple case to trigger on a secret creation
    func = AsyncMock()
    reg.add("before_apply", func)
    await reg.run("before_apply", "create", Secret("xxx"))
    func.assert_called_once()

    # Should not run on resource mismatch
    func = AsyncMock()
    reg.add("after_apply", func, resources=[Role, Hook])
    await reg.run("before_apply", "delete", Secret("xxx"))
    await reg.run("after_apply", "delete", Secret("xxx"))
    assert not func.called

    # Should not run on action mismatch
    func = AsyncMock()
    reg.add("after_apply", func, actions=["delete"])
    await reg.run("before_apply", "update", Secret("xxx"))
    await reg.run("after_apply", "update", Secret("xxx"))
    assert not func.called
