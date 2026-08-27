# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json
import click

from .appconfig import AppConfig
from .resources import Resources
from .options import generate_options, with_options

generate_options.add(
    click.option("--with-secrets/--without-secrets", "with_secrets", default=True)
)
generate_options.add(
    click.option(
        "--generated",
        metavar="PATH",
        default=None,
        help="Read the generated resource set from PATH (as produced by "
        "`tc-admin generate --json`) instead of generating it.",
    )
)


@with_options("generated")
async def resources(generated=None):
    """
    Generate the desired resources, or load a previously generated set from disk.
    """
    if generated:
        with open(generated) as f:
            return Resources.from_json(json.load(f))

    appconfig = AppConfig.current()
    resources = Resources()
    await appconfig.generators._call_all(resources)
    for mod in appconfig.modifiers:
        resources = await mod(resources)
    return resources
