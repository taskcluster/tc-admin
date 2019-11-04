# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import datetime
import random
import hashlib
import json

from .resources import Resource

FOREVER = datetime.datetime(3000, 1, 1, 0, 0, 0)

# this is a special semaphore value, whose presence is tested for with object
# identity (`is`).  It is used to indicate that no secret value has been
# provided.


class NoSecret:
    pass


# The per-run hash salt.  This ensures that hashes are different on every run
PER_RUN_SALT = str(random.randrange(2 ** 64)).encode("ascii")


def secret_formatter(id, value):
    """Format a secret value in a format that does not reveal the actual value, but
    still reliably identifies changes in the secret."""
    if value is NoSecret:
        return "<unknown>"
    m = hashlib.sha256()
    m.update(PER_RUN_SALT)
    m.update(id.encode("ascii"))
    m.update(json.dumps(value, sort_keys=True).encode("utf-8"))
    return m.hexdigest()[:10]


@attr.s
class Secret(Resource):
    name = attr.ib(type=str)
    secret = attr.ib(
        type=dict, default=NoSecret, metadata={"formatter": secret_formatter}
    )

    # NOTE: secrets managed by this library do not expire.

    def to_json(self):
        d = super(Secret, self).to_json()
        del d["secret"]
        return d

    @classmethod
    def from_json(self, json):
        # not clear what to do here, and `from_json` isn't widely used, so for
        # the moment this is not implemented
        raise NotImplementedError("from_json is not implemented for Secrets")

    @classmethod
    def from_api(cls, name, api_result=None):
        "Construct a new instance from the result of a taskcluster API call"
        return cls(name=name, secret=api_result["secret"] if api_result else NoSecret)

    def to_api(self):
        "Construct a payload for use with secrets.set"
        if not self.has_secret():
            raise ValueError("Cannot write a secret with no value")
        return {"expires": FOREVER, "secret": self.secret}

    def has_secret(self):
        "Return true if this secret has a value (is not NoSecret)"
        return self.secret is not NoSecret
