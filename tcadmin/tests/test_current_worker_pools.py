# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from tcadmin.resources import Resources
from tcadmin.current.worker_pools import fetch_worker_pools


pytestmark = pytest.mark.usefixtures("appconfig")


@pytest.fixture
def WorkerManager(mocker):
    """
    Mock out WorkerManager in tcadmin.current.worker_pools.

    The expected list of worker types should be set in WorkerManager.workerPools.
    """
    WorkerManager = mocker.patch("tcadmin.current.worker_pools.WorkerManager")
    WorkerManager.workerPools = []

    class FakeWorkerManager:
        async def listWorkerPools(self, query):
            limit = query.get("limit", 1)
            offset = int(query.get("continuationToken", "0"))
            res = {"workerPools": WorkerManager.workerPools[offset : offset + limit]}
            if offset + limit < len(WorkerManager.workerPools):
                res["continuationToken"] = str(offset + limit)
            return res

    WorkerManager.return_value = FakeWorkerManager()
    return WorkerManager


@pytest.mark.asyncio
async def test_fetch_worker_pools(WorkerManager):
    resources = Resources([], ["WorkerPool=managed*"])
    WorkerManager.workerPools = [
        {
            "config": {"is": "config"},
            "created": "2019-07-20T22:49:23.761Z",
            "lastModified": "2019-07-20T22:49:23.761Z",
            "workerPoolId": wpid,
            "description": "descr",
            "owner": "owner",
            "emailOnError": True,
            "providerId": "cirrus",
        }
        for wpid in ["managed-one", "unmanaged-two", "managed-three", "unmanaged-four"]
    ]
    await fetch_worker_pools(resources)
    assert [res.workerPoolId for res in resources] == ["managed-one", "managed-three"]
