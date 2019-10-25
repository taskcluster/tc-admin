# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import click

from .appconfig import AppConfig
from .resources import Resources
from .options import generate_options

generate_options.add(
    click.option("--with-secrets/--without-secrets", "with_secrets", default=True)
)


async def resources():
    """
    Generate the desired resources
    """
    appconfig = AppConfig.current()
    resources = Resources()
    await appconfig.generators._call_all(resources)
    for mod in appconfig.modifiers:
        resources = await mod(resources)
    return resources
