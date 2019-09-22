# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.generate.ciconfig.worker_pools import WorkerPool
from tcadmin.util.sessions import with_aiohttp_session


@pytest.mark.asyncio
@with_aiohttp_session
async def check_privileged_is_untrusted():
    """
    Ensures that any docker-worker pool with `allowPrivileged` is not
    run on a trusted image.
    """

    worker_pools = await WorkerPool.fetch_all()
    for pool in worker_pools:
        trusted = "trusted" in pool.config["image"]
        privileged = (
            pool.config.get("userData", {})
            .get("dockerConfig", {})
            .get("allowPrivileged", False)
        )
        assert not all(
            [trusted, privileged]
        ), f"{pool.worker_pool_id} has trusted CoT keys, but permits privileged (host-root-equivalent) tasks."
