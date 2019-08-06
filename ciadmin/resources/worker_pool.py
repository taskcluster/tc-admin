# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .resources import Resource
from .util import description_converter, json_formatter


@attr.s
class WorkerPool(Resource):
    workerPoolId = attr.ib(type=str)
    description = attr.ib(type=str, converter=description_converter)
    owner = attr.ib(type=str)
    config = attr.ib(type=dict, metadata={"formatter": json_formatter})
    emailOnError = attr.ib(type=bool)
    providerId = attr.ib(type=str)

    @property
    def id(self):
        return "{}={}".format(self.kind, self.workerPoolId)

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"

        return cls(
            workerPoolId=api_result["workerPoolId"],
            description=api_result["description"],
            owner=api_result["owner"],
            config=api_result["config"],
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
