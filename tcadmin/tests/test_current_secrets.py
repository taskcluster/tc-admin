# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from tcadmin.options import test_options
from tcadmin.resources import Resources, Secret
from tcadmin.current.secrets import fetch_secrets


@pytest.fixture
def Secrets(mocker):
    """
    Mock out Secrets in tcadmin.current.secrets.
    """
    Secrets = mocker.patch("tcadmin.current.secrets.Secrets")
    Secrets.secrets = []

    class FakeSecrets:
        async def list(self, query={}):
            limit = query.get("limit", 1)
            offset = int(query.get("continuationToken", "0"))
            res = {
                "secrets": [s["name"] for s in Secrets.secrets[offset : offset + limit]]
            }
            if offset + limit < len(Secrets.secrets):
                res["continuationToken"] = str(offset + limit)
            return res

        async def get(self, name):
            for secret in Secrets.secrets:
                if secret["name"] == name:
                    assert "secret" in secret
                    return secret
            raise KeyError("no such secret")

    Secrets.return_value = FakeSecrets()
    return Secrets


@pytest.mark.asyncio
async def test_fetch_secrets_empty(Secrets):
    "When there are no secrets, nothing happens"
    with test_options(with_secrets=True):
        resources = Resources([], [".*"])
        await fetch_secrets(resources)
        assert list(resources) == []


@pytest.mark.asyncio
async def test_fetch_secrets_managed(Secrets):
    "Only managed secrets are returned"
    with test_options(with_secrets=True):
        Secrets.secrets.append({"name": "secret1", "secret": "AA"})
        Secrets.secrets.append({"name": "unmanaged-secret2"})
        resources = Resources([], ["Secret=secret"])
        await fetch_secrets(resources)
        assert list(sorted(resources)) == [Secret(name="secret1", secret="AA")]


@pytest.mark.asyncio
async def test_fetch_secrets_without_secrets(Secrets):
    "When there are secrets but --without-secrets, we just get names"
    with test_options(with_secrets=False):
        Secrets.secrets.append({"name": "secret1"})
        Secrets.secrets.append({"name": "secret2"})
        resources = Resources([], [".*"])
        await fetch_secrets(resources)
        assert list(sorted(resources)) == [
            Secret(name="secret1"),
            Secret(name="secret2"),
        ]


@pytest.mark.asyncio
async def test_fetch_secrets_with_secrets(Secrets):
    "When there are secrets and --with-secrets, we get names and values"
    with test_options(with_secrets=True):
        Secrets.secrets.append({"name": "secret1", "secret": "AA"})
        Secrets.secrets.append({"name": "secret2", "secret": "BB"})
        resources = Resources([], [".*"])
        await fetch_secrets(resources)
        assert list(sorted(resources)) == [
            Secret(name="secret1", secret="AA"),
            Secret(name="secret2", secret="BB"),
        ]
