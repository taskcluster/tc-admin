# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json

import attr

from .resources import Resource
from .util import description_converter, json_formatter


@attr.s
class WorkerPool(Resource):
    workerPoolId = attr.ib(type=str)
    description = attr.ib(type=str, converter=description_converter)
    owner = attr.ib(type=str)
    config = attr.ib(
        type=dict,
        converter=lambda config: WorkerPool._sort_launch_configs(config),
        metadata={"formatter": json_formatter},
    )
    emailOnError = attr.ib(type=bool)
    providerId = attr.ib(type=str)

    @property
    def id(self):
        return "{}={}".format(self.kind, self.workerPoolId)

    @classmethod
    def _sort_launch_configs(cls, config):
        """Ensure launchConfigs are sorted by location for cleaner `tc-admin diff`,
        breaking ties by content since the API returns them in arbitrary order"""

        def sort_key(lc):
            if "zone" in lc:
                return lc["zone"]  # gcp
            if "location" in lc:
                return lc["location"]  # azure
            if "armDeployment" in lc:
                return lc["armDeployment"]["parameters"]["location"]["value"]  # azure ARM templates
            if "region" in lc:
                return lc["region"]  # aws
            return ""

        if "launchConfigs" in config:
            config = {
                **config,
                "launchConfigs": sorted(
                    config["launchConfigs"],
                    key=lambda lc: (sort_key(lc), json.dumps(lc, sort_keys=True)),
                ),
            }
        return config

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"
        return cls._construct_without_converters(
            workerPoolId=api_result["workerPoolId"],
            description=api_result["description"],
            owner=api_result["owner"],
            config=cls._sort_launch_configs(api_result["config"]),
            emailOnError=api_result["emailOnError"],
            providerId=api_result["providerId"],
        )

    def to_api(self):
        "Construct a payload for WorkerManager.{create,update}WorkerPool"

        return {
            "description": self.description,
            "owner": self.owner,
            "config": self.config,
            "emailOnError": self.emailOnError,
            "providerId": self.providerId,
        }
