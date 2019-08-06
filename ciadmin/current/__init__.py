# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
from ..resources import Resources
from . import hooks, roles, aws_provisioner_workertypes, worker_pools


async def resources(managed):
    """
    Fetch the existing resources that are managed by the provided list.
    """
    resources = Resources([], managed)

    await asyncio.gather(
        roles.fetch_roles(resources),
        hooks.fetch_hooks(resources),
        aws_provisioner_workertypes.fetch_aws_provisioner_workertypes(resources),
        worker_pools.fetch_worker_pools(resources),
    )
    return resources
