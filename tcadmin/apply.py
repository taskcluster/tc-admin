# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import click

from .resources import Resources
from .options import with_options, apply_options
from .update import Updater


apply_options.add(
    click.option("--grep", help="regular expression limiting resources updated")
)


@with_options("grep")
async def apply_changes(generated, current, grep):
    # limit the resources considered if --grep
    if grep:
        reg = re.compile(grep)
        generated = Resources(
            managed=generated.managed,
            resources=(r for r in generated.resources if reg.search(r.id)),
        )
        current = Resources(
            managed=current.managed,
            resources=(r for r in current.resources if reg.search(r.id)),
        )

    updater = await Updater.setup()
    await updater.update(generated, current)
