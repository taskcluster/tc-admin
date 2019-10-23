# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.aio import Auth
from taskcluster import optionsFromEnvironment

from ..resources import Client
from ..util.sessions import aiohttp_session


async def fetch_clients(resources):
    auth = Auth(optionsFromEnvironment(), session=aiohttp_session())
    query = {}
    while True:
        res = await auth.listClients(query=query)
        for clients in res["clients"]:
            client = Client.from_api(clients)
            if resources.is_managed(client.id):
                resources.add(client)

        if "continuationToken" in res:
            query["continuationToken"] = res["continuationToken"]
        else:
            break
