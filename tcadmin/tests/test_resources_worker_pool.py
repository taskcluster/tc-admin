# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import textwrap

from tcadmin.resources.worker_pool import WorkerPool


pytestmark = pytest.mark.usefixtures("appconfig")


@pytest.fixture(scope="module")
def simple_wp():
    return WorkerPool(
        workerPoolId="pp/ww",
        description="a workertype",
        owner="workertyper@example.com",
        config={"is": "config"},
        emailOnError=False,
        providerId="cirrus",
    )


def test_workertype_id(simple_wp):
    "An id is composed of the workerPoolId property"
    assert simple_wp.id == "WorkerPool=pp/ww"


def test_string_formatter(simple_wp):
    "Worker Types are properly formatted with a string"
    print(simple_wp)
    assert str(simple_wp) == textwrap.dedent(
        """\
        WorkerPool=pp/ww:
          workerPoolId: pp/ww
          description:
            *DO NOT EDIT* - This resource is configured automatically.

            a workertype
          owner: workertyper@example.com
          config:
            {
                "is": "config"
            }
          emailOnError: False
          providerId: cirrus"""  # noqa: E501, W291
    )


def test_role_from_api():
    "Worker Types are properly read from a Taskcluster API result"
    api_result = {
        "config": {"is": "config"},
        "created": "2019-07-20T22:49:23.761Z",
        "lastModified": "2019-07-20T22:49:23.761Z",
        "workerPoolId": "pp/ww",
        "description": "descr",
        "owner": "owner",
        "emailOnError": True,
        "providerId": "cirrus",
    }

    apwt = WorkerPool.from_api(api_result)
    assert apwt.workerPoolId == "pp/ww"
    assert apwt.config == {"is": "config"}
    assert apwt.description == textwrap.dedent(
        """\
            *DO NOT EDIT* - This resource is configured automatically.

            descr"""
    )
    assert apwt.owner == "owner"
    assert apwt.emailOnError is True
    assert apwt.providerId == "cirrus"


def test_to_api(simple_wp):
    "Worker Pools are properly converted to a Taskcluster API result"
    api_result = {
        "config": {"is": "config"},
        "description": textwrap.dedent(
            """\
            *DO NOT EDIT* - This resource is configured automatically.

            a workertype"""
        ),
        "owner": "workertyper@example.com",
        "emailOnError": False,
        "providerId": "cirrus",
    }
    assert simple_wp.to_api() == api_result
