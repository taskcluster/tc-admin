# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.aio import AwsProvisioner
from taskcluster import optionsFromEnvironment

from ..resources import AwsProvisionerWorkerType
from ..util.root_url import root_url
from ..util.sessions import aiohttp_session


async def fetch_aws_provisioner_workertypes(resources):
    # AWS provisioner only *exists* in this deployment:
    if root_url() != "https://taskcluster.net":
        return

    aws_provisioner = AwsProvisioner(
        optionsFromEnvironment(), session=aiohttp_session()
    )
    for workerTypeId in await aws_provisioner.listWorkerTypes():
        workerType = await aws_provisioner.workerType(workerTypeId)
        awsProvisionerWorkerType = AwsProvisionerWorkerType.from_api(workerType)
        if resources.is_managed(awsProvisionerWorkerType.id):
            resources.add(awsProvisionerWorkerType)
