# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .resources import Resource
from .util import description_converter, scopes_converter, list_formatter
from ..util.scopes import normalizeScopes


@attr.s
class Role(Resource):
    roleId = attr.ib(type=str)
    description = attr.ib(type=str, converter=description_converter)
    scopes = attr.ib(
        type=tuple, converter=scopes_converter, metadata={"formatter": list_formatter}
    )

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"
        return cls(
            roleId=api_result["roleId"],
            description=api_result["description"],
            scopes=api_result["scopes"],
        )

    def to_api(self):
        "Construct a payload for use with auth.createRole or auth.updateRole"
        return {"description": self.description, "scopes": self.scopes}

    def merge(self, other):
        assert self.roleId == other.roleId
        if self.description != other.description:
            raise RuntimeError(
                "Descriptions for {} to be merged differ".format(self.id)
            )
        scopes = normalizeScopes(self.scopes + other.scopes)
        return Role(roleId=self.roleId, description=self.description, scopes=scopes)
