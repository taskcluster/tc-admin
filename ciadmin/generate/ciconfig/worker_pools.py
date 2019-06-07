# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


@attr.s(frozen=True)
class WorkerPool:
    worker_pool_id = attr.ib(type=str)
    description = attr.ib(type=str)
    owner = attr.ib(type=str)
    provider_id = attr.ib(type=str)
    config = attr.ib()
    email_on_error = attr.ib(type=bool)

    @staticmethod
    async def fetch_all():
        """Load worker-type metadata from worker-pools.yml in ci-configuration"""
        worker_pools = await get_ciconfig_file("worker-pools.yml")
        for worker_pool_id in worker_pools:
            if worker_pool_id.count("/") != 1:
                raise ValueError(
                    "workerPoolid must be of the form `provisionerId/workerPool`"
                )
        return [
            WorkerPool(worker_pool_id=worker_pool_id, **info)
            for worker_pool_id, info in worker_pools.items()
        ]
