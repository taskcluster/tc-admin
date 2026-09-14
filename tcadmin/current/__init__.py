# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
from ..resources import Resources
from . import hooks, clients, roles, worker_pools, secrets

fetch_fns = {
    "Client": clients.fetch_clients,
    "Role": roles.fetch_roles,
    "Hook": hooks.fetch_hooks,
    "Secret": secrets.fetch_secrets,
    "WorkerPool": worker_pools.fetch_worker_pools,
}


async def resources(managed):
    """
    Fetch the existing resources that are managed by the provided list.
    """
    resources = Resources([], managed)

    kinds = {m.split("=", 1)[0] for m in managed}
    fetchers = {fetch_fns[kind](resources) for kind in kinds if kind in fetch_fns}
    await asyncio.gather(*fetchers)
    return resources
