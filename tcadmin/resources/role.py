# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .resources import Resource
from .util import Description, description_converter, scopes_converter, list_formatter
from ..util.scopes import normalizeScopes


@attr.s
class Role(Resource):
    roleId = attr.ib(type=str)
    description = attr.ib(type=Description, default="", converter=description_converter)
    scopes = attr.ib(
        type=tuple,
        default=(),
        converter=scopes_converter,
        metadata={"formatter": list_formatter},
    )

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"
        return cls._construct_without_converters(
            roleId=api_result["roleId"],
            description=api_result["description"],
            scopes=scopes_converter(api_result["scopes"]),
        )

    def to_api(self):
        "Construct a payload for use with auth.createRole or auth.updateRole"
        return {"description": self.description, "scopes": self.scopes}

    def merge(self, other):
        """
        Merge with another Role for the same roleId, unioning scopes.

        If only one side has a description, that description is used. If
        both sides have a description, the one on `self` (the left/existing
        side) wins.
        """
        assert self.roleId == other.roleId
        description = self.description if self.description.has_content else other.description
        scopes = normalizeScopes(self.scopes + other.scopes)
        return Role(roleId=self.roleId, description=description, scopes=scopes)
