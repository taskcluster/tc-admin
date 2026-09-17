# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import regex
from taskcluster.aio import Hooks

from ..resources import Hook
from ..util.sessions import aiohttp_session
from ..util.taskcluster import tcClientOptions


async def fetch_hooks(resources):
    hooks = Hooks(await tcClientOptions(), session=aiohttp_session())
    for hookGroupId in (await hooks.listHookGroups())["groups"]:
        idPrefix = "Hook={}/".format(hookGroupId)
        # If no managed pattern could match this hookGroupId, avoid calling the
        # Taskcluster API. We use the `regex` package for partial match
        # support.
        is_managed = any(
            regex.match(m.include, idPrefix, partial=True) for m in resources.managed
        )
        if not is_managed:
            continue
        for hook in (await hooks.listHooks(hookGroupId))["hooks"]:
            hook = Hook.from_api(hook)
            if resources.is_managed(hook.id):
                resources.add(hook)
