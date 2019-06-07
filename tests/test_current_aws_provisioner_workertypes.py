# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.resources import Resources, AwsProvisionerWorkerType
from ciadmin.current.aws_provisioner_workertypes import (
    fetch_aws_provisioner_workertypes,
)


@pytest.fixture
def AwsProvisioner(mocker):
    """
    Mock out AwsProvisioner in ciadmin.current.aws_provisioner_workertypes.

    The expected list of worker types should be set in AwsProvisioner.workerTypes.
    """
    AwsProvisioner = mocker.patch(
        "ciadmin.current.aws_provisioner_workertypes.AwsProvisioner"
    )
    AwsProvisioner.workerTypes = []
    AwsProvisioner.listHookCalls = []

    class FakeAwsProvisioner:
        async def listWorkerTypes(self):
            return list(sorted(wt["workerType"] for wt in AwsProvisioner.workerTypes))

        async def workerType(self, workerTypeId):
            for workerType in AwsProvisioner.workerTypes:
                if workerType["workerType"] == workerTypeId:
                    return workerType

    AwsProvisioner.return_value = FakeAwsProvisioner()
    return AwsProvisioner


@pytest.mark.asyncio
async def test_fetch_aws_provisioner_workertypes(AwsProvisioner):
    resources = Resources([], ["AwsProvisionerWorkerType=managed*"])
    AwsProvisioner.workerTypes = [
        {
            "workerType": workerTypeId,
            "launchSpec": {"SecurityGroups": ["docker-worker"]},
            "description": "** WRITE THIS**",
            "owner": "** WRITE THIS **",
            "userData": {},
            "minCapacity": 0,
            "maxCapacity": 200,
            "scalingRatio": 0,
            "minPrice": 4,
            "maxPrice": 4.2,
            "instanceTypes": [],
            "regions": [],
            "availabilityZones": [],
        }
        for workerTypeId in ["managed-one", "unmanaged-two"]
    ]
    await fetch_aws_provisioner_workertypes(resources)
    assert [res.workerType for res in resources] == ["managed-one"]
