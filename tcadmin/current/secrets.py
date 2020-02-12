# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.aio import Secrets

from ..options import with_options
from ..resources import Secret
from ..util.sessions import aiohttp_session
from ..util.taskcluster import optionsFromEnvironment


@with_options("with_secrets")
async def fetch_secrets(resources, with_secrets):
    api = Secrets(optionsFromEnvironment(), session=aiohttp_session())
    query = {}
    while True:
        res = await api.list(query=query)
        for secret_name in res["secrets"]:
            if resources.is_managed("Secret={}".format(secret_name)):
                # only call `get` if we are managing secrets
                if with_secrets:
                    getres = await api.get(secret_name)
                    secret = Secret.from_api(secret_name, getres)
                else:
                    secret = Secret.from_api(secret_name)
                resources.add(secret)

        if "continuationToken" in res:
            query["continuationToken"] = res["continuationToken"]
        else:
            break
