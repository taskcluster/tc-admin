# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster import optionsFromEnvironment
import os

from .root_url import root_url


async def tcClientOptions():
    """Build Taskcluster client options, supporting proxy and getting root_url
    from the appconfig"""
    if "TASKCLUSTER_PROXY_URL" in os.environ:
        return {"rootUrl": os.environ["TASKCLUSTER_PROXY_URL"]}
    else:
        options = optionsFromEnvironment()
        options["rootUrl"] = await root_url()
        return options
