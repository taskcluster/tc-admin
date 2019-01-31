# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file

DEFAULT_INPUT_SCHEMA = {
    "anyOf": [
        {"type": "object", "description": "user input for the task"},
        {"const": None, "description": "null when the action takes no input"},
    ]
}


@attr.s(frozen=True)
class Action:
    trust_domain = attr.ib(type=str)
    level = attr.ib(type=int)
    action_perm = attr.ib(type=str)
    input_schema = attr.ib(default=DEFAULT_INPUT_SCHEMA)

    @staticmethod
    async def fetch_all():
        """Load project metadata from actions.yml in ci-configuration"""
        actions = await get_ciconfig_file("actions.yml")
        return [Action(**info) for info in actions]
