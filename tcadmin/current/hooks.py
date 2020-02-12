# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.aio import Hooks

from ..resources import Hook
from ..util.sessions import aiohttp_session
from ..util.taskcluster import optionsFromEnvironment


async def fetch_hooks(resources):
    hooks = Hooks(optionsFromEnvironment(), session=aiohttp_session())
    for hookGroupId in (await hooks.listHookGroups())["groups"]:
        idPrefix = "Hook={}/".format(hookGroupId)
        # if no hook with this hookGroupId is managed, skip it
        is_managed = any(m.startswith(idPrefix) for m in resources.managed)
        is_managed = is_managed or resources.is_managed(idPrefix)
        if not is_managed:
            continue
        for hook in (await hooks.listHooks(hookGroupId))["hooks"]:
            hook = Hook.from_api(hook)
            if resources.is_managed(hook.id):
                resources.add(hook)
