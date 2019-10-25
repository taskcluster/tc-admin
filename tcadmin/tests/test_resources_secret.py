# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import textwrap
import pytest
import datetime

from tcadmin.resources import Secret
from tcadmin.resources.secret import FOREVER, NoSecret


def test_secret_formatter():
    "Secrets are properly formatted with a string"
    secret = Secret("my-secret", {"password": "hunter2"})
    # check that the formatter is stable
    assert str(secret) == str(secret)
    assert re.sub(
        r"secret: [a-z0-9]+", "secret: <hash>", str(secret)
    ) == textwrap.dedent(
        """\
        Secret=my-secret:
          name: my-secret
          secret: <hash>"""
    )


def test_secret_formatter_no_secret():
    "Secrets with no secret are properly formatted with a string"
    secret = Secret("my-secret")
    # check that the formatter is stable
    assert str(secret) == str(secret)
    assert str(secret) == textwrap.dedent(
        """\
        Secret=my-secret:
          name: my-secret
          secret: <unknown>"""
    )


def test_secret_formatter_different_secrets():
    "Secrets are properly formatted with a string"
    secret1 = Secret("my-secret1", {"password": "hunter2"})
    secret2 = Secret("my-secret2", {"password": "hunter2"})
    # even though these have the same value, they should format their last lines differently
    fmt1 = str(secret1)
    fmt2 = str(secret2)
    assert fmt1.split("\n")[-1] != fmt2.split("\n")[-1]


def test_secret_json():
    "Secrets are properly output as JSON, including the description preamble and sorted scopes"
    secret = Secret("my-secret", {"password": "hunter2"})
    assert secret.to_json() == {"name": "my-secret", "kind": "Secret"}


def test_secret_from_api():
    "Secrets are properly read from a Taskcluster API result"
    api_result = {
        "expires": datetime.datetime(3000, 1, 1, 0, 0, 0),
        "secret": {"password": "hunter3"},
    }
    secret = Secret.from_api("my-secret", api_result)
    assert secret.name == "my-secret"
    assert secret.secret == {"password": "hunter3"}


def test_secret_from_api_no_secret():
    "Secrets are properly read from a Taskcluster API result"
    secret = Secret.from_api("my-secret")
    assert secret.name == "my-secret"
    assert secret.secret == NoSecret


def test_secret_to_api():
    "Secrets are properly output to the API, including the actual secret value"
    secret = Secret("my-secret", {"password": "hunter2"})
    assert secret.to_api() == {"expires": FOREVER, "secret": {"password": "hunter2"}}


def test_secret_to_api_no_secret():
    "A secret with no value is not output to the API"
    secret = Secret("my-secret")

    with pytest.raises(ValueError):
        secret.to_api()
