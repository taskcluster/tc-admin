# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.aio import WorkerManager

from ..resources import WorkerPool
from ..util.sessions import aiohttp_session
from ..util.taskcluster import tcClientOptions


async def fetch_worker_pools(resources):
    worker_manager = WorkerManager(await tcClientOptions(), session=aiohttp_session())
    query = {}
    while True:
        res = await worker_manager.listWorkerPools(query=query)
        for wp in res["workerPools"]:
            workerPool = WorkerPool.from_api(wp)

            # Worker-manager does not allow pools to be deleted; instead, they
            # are given providerId "null-provider", which provides no workers.
            # Once any pre-existing workers are gone, the service will delete
            # the pool.  So, we ignore any null-provider worker pools on the
            # assumption that they will be delete dsoon.
            if workerPool.providerId == "null-provider":
                continue

            if resources.is_managed(workerPool.id):
                resources.add(workerPool)

        if "continuationToken" in res:
            query["continuationToken"] = res["continuationToken"]
        else:
            break
