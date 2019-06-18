# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import click

from ..resources import Resources
from ..options import decorate, with_click_options
from .modifier import Modifier


def options(fn):
    return decorate(
        fn,
        click.option("--grep", help="regular expression limiting resources displayed"),
    )


@with_click_options("grep")
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

    modifier = Modifier()
    await modifier.modify(generated, current)
