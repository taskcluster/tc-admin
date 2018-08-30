# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


@attr.s(frozen=True)
class Action:
    trust_domain = attr.ib(type=str)
    level = attr.ib(type=int)
    action_perm = attr.ib(type=str)
    groups = attr.ib(type=tuple, converter=lambda v: tuple(v))

    @staticmethod
    async def fetch_all():
        """Load project metadata from actions.yml in ci-configuration"""
        actions = await get_ciconfig_file('actions.yml')
        return [Action(**info) for info in actions]
