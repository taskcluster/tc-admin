# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .resources import Resource
from .util import description_converter, list_formatter, json_formatter


def schedule_converter(value):
    """Ensure that schedules are always immutable (a tuple)"""
    return tuple(value)


@attr.s
class Hook(Resource):
    hookGroupId = attr.ib(type=str)
    hookId = attr.ib(type=str)
    name = attr.ib(type=str)
    description = attr.ib(type=str, converter=description_converter)
    owner = attr.ib(type=str)
    emailOnError = attr.ib(type=bool)
    schedule = attr.ib(
        type=tuple, converter=schedule_converter, metadata={"formatter": list_formatter}
    )
    task = attr.ib(type=dict, metadata={"formatter": json_formatter})
    triggerSchema = attr.ib(type=dict, metadata={"formatter": json_formatter})

    @property
    def id(self):
        return "{}={}/{}".format(self.kind, self.hookGroupId, self.hookId)

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"
        return cls(
            hookId=api_result["hookId"],
            hookGroupId=api_result["hookGroupId"],
            # flatten the metadata sub-key
            description=api_result["metadata"]["description"],
            name=api_result["metadata"]["name"],
            owner=api_result["metadata"]["owner"],
            emailOnError=api_result["metadata"]["emailOnError"],
            schedule=api_result["schedule"],
            task=api_result["task"],
            triggerSchema=api_result["triggerSchema"],
        )

    def to_api(self):
        "Construct a payload for Hooks.createHook and Hooks.updateHook"
        return {
            "hookGroupId": self.hookGroupId,
            "hookId": self.hookId,
            "metadata": {
                "name": self.name,
                "description": self.description,
                "owner": self.owner,
                "emailOnError": self.emailOnError,
            },
            "schedule": self.schedule,
            "task": self.task,
            "triggerSchema": self.triggerSchema,
        }
