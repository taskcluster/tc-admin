# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .resources import Resource
from .util import description_converter, json_formatter


@attr.s
class AwsProvisionerWorkerType(Resource):
    workerType = attr.ib(type=str)
    launchSpec = attr.ib(type=dict, metadata={"formatter": json_formatter})
    description = attr.ib(type=str, converter=description_converter)
    owner = attr.ib(type=str)
    # secrets is omitted
    userData = attr.ib(type=dict, metadata={"formatter": json_formatter})
    # scopes is omitted
    minCapacity = attr.ib(type=int)
    maxCapacity = attr.ib(type=int)
    scalingRatio = attr.ib(type=float)
    # minPrice omitted
    # maxPrice omitted
    # canUseOndemand omitted
    # canUseSpot omitted
    # lastModified omitted
    instanceTypes = attr.ib(type=list, metadata={"formatter": json_formatter})
    regions = attr.ib(type=list, metadata={"formatter": json_formatter})
    availabilityZones = attr.ib(type=list, metadata={"formatter": json_formatter})

    @property
    def id(self):
        return "{}={}".format(self.kind, self.workerType)

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"

        def drop_fields(d):
            d = d.copy()
            if "secrets" in d:
                del d["secrets"]
            if "scopes" in d:
                del d["scopes"]
            return d

        def drop_az_fields(d):
            d = drop_fields(d)
            if "region" in d:
                del d["region"]
            return d

        return cls(
            workerType=api_result["workerType"],
            launchSpec=api_result["launchSpec"],
            description=api_result["description"],
            owner=api_result["owner"],
            userData=api_result["userData"],
            minCapacity=api_result["minCapacity"],
            maxCapacity=api_result["maxCapacity"],
            scalingRatio=api_result["scalingRatio"],
            instanceTypes=[drop_fields(i) for i in api_result["instanceTypes"]],
            regions=[drop_fields(r) for r in api_result["regions"]],
            availabilityZones=[
                drop_az_fields(a) for a in api_result["availabilityZones"]
            ],
        )

    def to_api(self):
        "Construct a payload for AwsProvisioner.{create,update}WorkerType"

        def add_fields(d):
            d = d.copy()
            d["secrets"] = {}
            d["scopes"] = []
            return d

        def add_az_fields(d):
            d = d.copy()
            d["secrets"] = {}
            d["region"] = d["availabilityZone"][:-1]
            return d

        return {
            "launchSpec": self.launchSpec,
            "description": self.description,
            "owner": self.owner,
            "secrets": {},
            "userData": self.userData,
            "minCapacity": self.minCapacity,
            "maxCapacity": self.maxCapacity,
            "scalingRatio": self.scalingRatio,
            "minPrice": 8,  # value ignored by provisioner
            "maxPrice": 8,  # value ignored by provisioner
            "canUseOndemand": True,  # value ignored by provisioner
            "canUseSpot": True,  # value ignored by provisioner
            "instanceTypes": [add_fields(i) for i in self.instanceTypes],
            "regions": [add_fields(r) for r in self.regions],
            "availabilityZones": [add_az_fields(a) for a in self.availabilityZones],
            "scopes": [],
        }
