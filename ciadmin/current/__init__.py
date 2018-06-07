# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
from ..resources import Resources
from . import hooks, roles


async def resources(managed):
    '''
    Fetch the existing resources that are managed by the provided list.
    '''
    resources = Resources([], managed)

    await asyncio.gather(
        roles.fetch_roles(resources),
        hooks.fetch_hooks(resources),
    )
    return resources
