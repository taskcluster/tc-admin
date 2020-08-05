# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from tcadmin.resources import Resources, Client
from tcadmin.current.clients import fetch_clients


pytestmark = pytest.mark.usefixtures("appconfig")


@pytest.fixture
def AuthForClients(mocker):
    """
    Mock out Auth in tcadmin.current.clients.

    The expected return value for listClients should be set in Auth.clients
    """
    Auth = mocker.patch("tcadmin.current.clients.Auth")
    Auth.clients = []

    class FakeAuth:
        async def listClients(self, query={}):
            limit = query.get("limit", 1)
            offset = int(query.get("continuationToken", "0"))
            res = {"clients": Auth.clients[offset : offset + limit]}
            if offset + limit < len(Auth.clients):
                res["continuationToken"] = str(offset + limit)
            return res

    Auth.return_value = FakeAuth()
    return Auth


@pytest.fixture
def make_client():
    def make_client(**kwargs):
        kwargs.setdefault("clientId", "test-client")
        kwargs.setdefault("description", "descr")
        kwargs.setdefault("scopes", ["scope-a"])
        return kwargs

    return make_client


@pytest.mark.asyncio
async def test_fetch_clients_empty(AuthForClients):
    "When there are no clients, nothing happens"
    resources = Resources([], [".*"])
    await fetch_clients(resources)
    assert list(resources) == []


@pytest.mark.asyncio
async def test_fetch_clients_managed(AuthForClients, make_client):
    "When a client is present and managed, it is included"
    resources = Resources([], [".*"])
    api_client = make_client()
    AuthForClients.clients.append(api_client)
    await fetch_clients(resources)
    assert list(resources) == [Client.from_api(api_client)]


@pytest.mark.asyncio
async def test_fetch_clients_unmanaged(AuthForClients, make_client):
    "When a client is present and unmanaged, it is not included"
    resources = Resources([], ["Client=managed*"])
    api_client1 = make_client(clientId="managed-client")
    api_client2 = make_client(clientId="un-managed-client")
    AuthForClients.clients.extend([api_client1, api_client2])
    await fetch_clients(resources)
    assert list(resources) == [Client.from_api(api_client1)]
