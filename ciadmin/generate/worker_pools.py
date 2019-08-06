# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import copy

from ..resources import AwsProvisionerWorkerType, WorkerPool
from .ciconfig.worker_pools import WorkerPool as ConfigWorkerPool
from .ciconfig.worker_images import WorkerImage


def full_instance_pool(i):
    i.setdefault("capacity", 1)
    i.setdefault("utility", 1)
    i.setdefault("launchSpec", {})
    i.setdefault("userData", {})
    return i


def full_region(r):
    r.setdefault("launchSpec", {})
    r.setdefault("userData", {})
    return r


def full_availability_zone(a):
    a.setdefault("launchSpec", {})
    a.setdefault("userData", {})
    return a


def set_ec2_worker_images(config, worker_images):
    """Set region[i].launchSpec.ImageId based on the ci-admin-specific top-level
    field "image", then delete that field"""

    if "image" not in config:
        return config

    config = copy.deepcopy(config)
    image = worker_images[config.pop("image")]

    for region in config.get("regions", []):
        region_name = region["region"]
        resolved_image = image.image_id("ec2", region_name)
        region.setdefault("launchSpec", {})["ImageId"] = resolved_image

    return config


async def make_worker_pool(resources, environment, wp, worker_images):
    legacy_env = environment.root_url == "https://taskcluster.net"
    legacy_wt = wp.provider_id == "legacy-aws-provisioner-v1"

    # do not try to provision legacy worker pools in a non-legacy environment.
    if not legacy_env and legacy_wt:
        return

    if legacy_wt:
        return await make_aws_provisioner_worker_type(
            resources, environment, wp, worker_images
        )

    return WorkerPool(
        workerPoolId=wp.worker_pool_id,
        description=wp.description,
        owner=wp.owner,
        providerId=wp.provider_id,
        config=wp.config,
        emailOnError=wp.email_on_error,
    )


async def make_aws_provisioner_worker_type(resources, environment, wp, worker_images):
    if wp.email_on_error:
        raise RuntimeError(
            "email_on_error is not supported for legacy-aws-provisioner-v1"
        )

    provisionerId, workerType = wp.worker_pool_id.split("/")

    # TODO: once all worker-pools are managed (including generic-worker), we can just manage
    # AwsProvisionerWorkerType=*
    resources.manage("AwsProvisionerWorkerType={}".format(workerType))

    # Fill out the config more fully to feed to aws provisioner
    config = set_ec2_worker_images(wp.config, worker_images)
    return AwsProvisionerWorkerType(
        workerType=workerType,
        description=wp.description,
        owner=wp.owner,
        launchSpec=config.get("launchSpec", {}),
        userData=config.get("userData", {}),
        minCapacity=config.get("minCapacity", 0),
        maxCapacity=config["maxCapacity"],
        scalingRatio=config.get("scalingRatio", 0),
        instanceTypes=[full_instance_pool(i) for i in config.get("instanceTypes", [])],
        regions=[full_region(r) for r in config.get("regions", [])],
        availabilityZones=[
            full_availability_zone(a) for a in config.get("availabilityZones", [])
        ],
    )


async def update_resources(resources, environment):
    """
    Manage the worker-pool configurations
    """
    worker_pools = await ConfigWorkerPool.fetch_all()
    worker_images = await WorkerImage.fetch_all()

    resources.manage("WorkerPool=*")

    for wp in worker_pools:
        apwt = await make_worker_pool(resources, environment, wp, worker_images)
        if apwt:
            resources.add(apwt)
