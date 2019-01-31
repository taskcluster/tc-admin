# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


@attr.s(frozen=True)
class Environment:
    environment = attr.ib(type=str)
    root_url = attr.ib(type=str)
    modify_resources = attr.ib(type=list, factory=lambda: [])

    @staticmethod
    async def fetch_all():
        """Load environment data from environments.yml in ci-configuration"""
        environments = await get_ciconfig_file("environments.yml")
        return [
            Environment(environment, **info)
            for environment, info in environments.items()
        ]
