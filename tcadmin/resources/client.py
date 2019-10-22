# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import datetime

from .resources import Resource
from .util import description_converter, scopes_converter, list_formatter
from ..util.scopes import normalizeScopes

FOREVER = datetime.datetime(3000, 1, 1, 0, 0, 0)


@attr.s
class Client(Resource):
    clientId = attr.ib(type=str)
    description = attr.ib(type=str, converter=description_converter)
    scopes = attr.ib(
        type=tuple, converter=scopes_converter, metadata={"formatter": list_formatter}
    )

    # NOTE: clients are managed like roles.  Any associated access tokens are
    # not handled by this library.  Where clients are needed, their access
    # tokens should be reset manually and the resulting accessToken used as
    # necessary.  Like roles, the clients managed here last "forever".

    @classmethod
    def from_api(cls, api_result):
        "Construct a new instance from the result of a taskcluster API call"
        return cls(
            clientId=api_result["clientId"],
            description=api_result["description"],
            scopes=api_result["scopes"],
        )

    def to_api(self):
        "Construct a payload for use with auth.createClient or auth.updateClient"
        return {
            "description": self.description,
            "scopes": self.scopes,
            "expires": FOREVER,
            "deleteOnExpiration": False,
        }

    def merge(self, other):
        assert self.clientId == other.clientId
        if self.description != other.description:
            raise RuntimeError(
                "Descriptions for {} to be merged differ".format(self.id)
            )
        scopes = normalizeScopes(self.scopes + other.scopes)
        return Client(
            clientId=self.clientId, description=self.description, scopes=scopes
        )
