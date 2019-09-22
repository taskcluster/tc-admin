# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr


@attr.s(frozen=True)
class Environment:
    # Environment name
    environment = attr.ib(type=str)

    # Root URL for this environment
    root_url = attr.ib(type=str)

    # List of modifications to make to the generated resources for this
    # environment.  This is useful, for example, for modifying staging
    # environments to consume fewer resources.
    modify_resources = attr.ib(type=list, factory=lambda: [])
