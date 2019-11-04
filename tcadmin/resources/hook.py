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


def bindings_converter(value):
    """Convert a list to a tuple to ensure immutability"""
    return tuple(sorted(value))


def bindings_validator(instance, attribute, value):
    """Ensure that bindings are always a sequence of Bindings"""
    if not all(isinstance(v, Binding) for v in value):
        raise ValueError("bindings must be a sequence of Binding instances")


def bindings_formatter(id, value):
    """Format bindings as a list of bulleted strings"""
    return "\n".join("- {}".format(v) for v in value)


@attr.s
class Binding(object):
    exchange = attr.ib(type=str)
    routingKeyPattern = attr.ib(type=str)

    @classmethod
    def from_api(cls, api_result):
        return cls(**api_result)


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
    bindings = attr.ib(
        type=tuple,
        converter=bindings_converter,
        validator=bindings_validator,
        metadata={"formatter": bindings_formatter},
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
            bindings=tuple(Binding.from_api(b) for b in api_result["bindings"]),
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
            "bindings": [
                {"exchange": v.exchange, "routingKeyPattern": v.routingKeyPattern}
                for v in self.bindings
            ],
            "task": self.task,
            "triggerSchema": self.triggerSchema,
        }
