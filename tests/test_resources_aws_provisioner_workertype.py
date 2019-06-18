# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import textwrap

from ciadmin.resources.aws_provisioner_workertype import AwsProvisionerWorkerType


@pytest.fixture(scope="module")
def simple_wt():
    return AwsProvisionerWorkerType(
        workerType="wt",
        launchSpec={"is": "launchspec"},
        description="a workertype",
        owner="workertyper@example.com",
        userData={"is": "userData"},
        minCapacity=1,
        maxCapacity=101,
        scalingRatio=0.5,
        instanceTypes=[{"is": "instanceType"}],
        regions=[{"is": "region"}],
        availabilityZones=[{"is": "availabilityZone"}],
    )


def test_workertype_id(simple_wt):
    "An id is composed of the workerType property"
    assert simple_wt.id == "AwsProvisionerWorkerType=wt"


def test_string_formatter(simple_wt):
    "Worker Types are properly formatted with a string"
    print(simple_wt)
    assert str(simple_wt) == textwrap.dedent(
        """\
        AwsProvisionerWorkerType=wt:
          workerType: wt
          launchSpec:
            {
                "is": "launchspec"
            }
          description:
            *DO NOT EDIT* - This resource is configured automatically by [ci-admin](https://hg.mozilla.org/ci/ci-admin).

            a workertype
          owner: workertyper@example.com
          userData:
            {
                "is": "userData"
            }
          minCapacity: 1
          maxCapacity: 101
          scalingRatio: 0.5
          instanceTypes:
            [
                {
                    "is": "instanceType"
                }
            ]
          regions:
            [
                {
                    "is": "region"
                }
            ]
          availabilityZones:
            [
                {
                    "is": "availabilityZone"
                }
            ]"""  # noqa: E501, W291
    )


def test_role_from_api():
    "Worker Types are properly read from a Taskcluster API result"
    api_result = {
        "workerType": "ami-test-pv",
        "launchSpec": {"SecurityGroups": ["docker-worker"]},
        "description": "** WRITE THIS**",
        "owner": "** WRITE THIS **",
        "secrets": {},
        "userData": {"dockerConfig": {"allowPrivileged": False}},
        "scopes": [
            "assume:worker-type:aws-provisioner-v1/ami-test-pv",
            "assume:worker-id:*",
        ],
        "minCapacity": 0,
        "maxCapacity": 200,
        "scalingRatio": 0,
        "minPrice": 4,
        "maxPrice": 4.2,
        "canUseOndemand": False,
        "canUseSpot": True,
        "instanceTypes": [
            {
                "capacity": 1,
                "instanceType": "m1.medium",
                "launchSpec": {},
                "scopes": [],
                "secrets": {},
                "userData": {"capacityManagement": {"diskspaceThreshold": 2000000000}},
                "utility": 1,
            }
        ],
        "regions": [
            {
                "launchSpec": {"ImageId": "ami-d34268a9"},
                "region": "us-east-1",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-0c474a6c"},
                "region": "us-west-1",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-60d46918"},
                "region": "us-west-2",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
        ],
        "availabilityZones": [],
    }

    apwt = AwsProvisionerWorkerType.from_api(api_result)
    assert apwt.workerType == "ami-test-pv"
    assert apwt.launchSpec == {"SecurityGroups": ["docker-worker"]}
    assert apwt.description == textwrap.dedent(
        """\
            *DO NOT EDIT* - This resource is configured automatically by [ci-admin](https://hg.mozilla.org/ci/ci-admin).

            ** WRITE THIS**"""
    )
    assert apwt.owner == "** WRITE THIS **"
    assert apwt.userData == {"dockerConfig": {"allowPrivileged": False}}
    assert apwt.minCapacity == 0
    assert apwt.maxCapacity == 200
    assert apwt.scalingRatio == 0
    assert apwt.instanceTypes == [
        {
            "capacity": 1,
            "instanceType": "m1.medium",
            "launchSpec": {},
            "userData": {"capacityManagement": {"diskspaceThreshold": 2000000000}},
            "utility": 1,
        }
    ]
    assert apwt.regions == [
        {
            "launchSpec": {"ImageId": "ami-d34268a9"},
            "region": "us-east-1",
            "userData": {},
        },
        {
            "launchSpec": {"ImageId": "ami-0c474a6c"},
            "region": "us-west-1",
            "userData": {},
        },
        {
            "launchSpec": {"ImageId": "ami-60d46918"},
            "region": "us-west-2",
            "userData": {},
        },
    ]
    assert apwt.availabilityZones == []


def test_role_to_api():
    "Worker Types are properly converted to a Taskcluster API result"
    api_result = {
        "launchSpec": {"SecurityGroups": ["docker-worker"]},
        "description": textwrap.dedent(
            """\
            *DO NOT EDIT* - This resource is configured automatically by [ci-admin](https://hg.mozilla.org/ci/ci-admin).

            ** WRITE THIS**"""
        ),
        "owner": "** WRITE THIS **",
        "secrets": {},
        "userData": {"dockerConfig": {"allowPrivileged": False}},
        "minCapacity": 0,
        "maxCapacity": 200,
        "scalingRatio": 0,
        "minPrice": 8,
        "maxPrice": 8,
        "instanceTypes": [
            {
                "capacity": 1,
                "instanceType": "m1.medium",
                "launchSpec": {},
                "scopes": [],
                "secrets": {},
                "userData": {"capacityManagement": {"diskspaceThreshold": 2000000000}},
                "utility": 1,
            }
        ],
        "regions": [
            {
                "launchSpec": {"ImageId": "ami-d34268a9"},
                "region": "us-east-1",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-0c474a6c"},
                "region": "us-west-1",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-60d46918"},
                "region": "us-west-2",
                "scopes": [],
                "secrets": {},
                "userData": {},
            },
        ],
        "availabilityZones": [],
        "scopes": [],
    }

    apwt = AwsProvisionerWorkerType(
        workerType="ami-test-pv",
        launchSpec={"SecurityGroups": ["docker-worker"]},
        description="** WRITE THIS**",
        owner="** WRITE THIS **",
        userData={"dockerConfig": {"allowPrivileged": False}},
        minCapacity=0,
        maxCapacity=200,
        scalingRatio=0,
        instanceTypes=[
            {
                "capacity": 1,
                "instanceType": "m1.medium",
                "launchSpec": {},
                "userData": {"capacityManagement": {"diskspaceThreshold": 2000000000}},
                "utility": 1,
            }
        ],
        regions=[
            {
                "launchSpec": {"ImageId": "ami-d34268a9"},
                "region": "us-east-1",
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-0c474a6c"},
                "region": "us-west-1",
                "userData": {},
            },
            {
                "launchSpec": {"ImageId": "ami-60d46918"},
                "region": "us-west-2",
                "userData": {},
            },
        ],
        availabilityZones=[],
    )

    assert apwt.to_api() == api_result
