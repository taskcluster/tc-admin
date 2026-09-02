# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import textwrap

from tcadmin.resources.resources import Resource
from tcadmin.resources.client import Client


pytestmark = pytest.mark.usefixtures("appconfig")


def test_client_formatter():
    "Clients are properly formatted with a string, including the description preamble and sorted scopes"
    client = Client("my:client-id", "This is my client", ["b", "a", "c"])
    assert str(client) == textwrap.dedent(
        """\
        Client=my:client-id:
          clientId: my:client-id
          description:
            *DO NOT EDIT* - This resource is configured automatically.
            
            This is my client
          scopes:
            - a
            - b
            - c"""  # noqa: E501, W293
    )


def test_client_json():
    "Clients are properly output as JSON, including the description preamble and sorted scopes"
    client = Client("my:client-id", "This is my client", ["b", "a", "c"])
    assert client == Resource.from_json(client.to_json())
    assert client.to_json() == {
        "clientId": "my:client-id",
        "kind": "Client",
        "description": "*DO NOT EDIT* - This resource is configured automatically.\n\nThis is my client",
        "scopes": ["a", "b", "c"],
    }


def test_client_from_api():
    "Clients are properly read from a Taskcluster API result"
    api_result = {
        "clientId": "my:client-id",
        "description": "*DO NOT EDIT* - This resource is configured automatically.\n\nThis is my client",
        "scopes": ["scope-a", "scope-b"],
    }
    client = Client.from_api(api_result)
    assert client.clientId == "my:client-id"
    assert client.description == api_result["description"]
    assert client.scopes == ("scope-a", "scope-b")


def test_client_merge_simple():
    "Clients with matching descriptions can be merged"
    r1 = Client(clientId="client", description="test", scopes=["a"])
    r2 = Client(clientId="client", description="test", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.clientId == "client"
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")


def test_client_merge_normalized():
    "Scopes are normalized when merging"
    r1 = Client(clientId="client", description="test", scopes=["a", "b*"])
    r2 = Client(clientId="client", description="test", scopes=["a", "bcdef", "c*"])
    merged = r1.merge(r2)
    assert merged.clientId == "client"
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b*", "c*")


def test_client_merge_different_descr():
    "When both sides have a description, the left (self) side wins"
    r1 = Client(clientId="client", description="test1", scopes=["a"])
    r2 = Client(clientId="client", description="test2", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.description.endswith("test1")
    assert merged.scopes == ("a", "b")


def test_client_merge_missing_description_uses_other_side():
    "If only one side has a description, that description is used"
    with_descr = Client(clientId="client", description="test", scopes=["a"])
    without_descr = Client(clientId="client", scopes=["b"])

    merged = without_descr.merge(with_descr)
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")

    merged = with_descr.merge(without_descr)
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")


def test_client_merge_neither_has_description(appconfig):
    "If neither side has a description, the merged client has none either"
    r1 = Client(clientId="client", scopes=["a"])
    r2 = Client(clientId="client", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.description == appconfig.description_prefix
    assert merged.scopes == ("a", "b")


def test_client_description_is_optional(appconfig):
    "A client can be constructed without a description at all"
    client = Client(clientId="client", scopes=["a"])
    assert client.description == appconfig.description_prefix
