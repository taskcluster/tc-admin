# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import functools
import click
import asyncio
import sys

from .util.sessions import with_aiohttp_session
from . import generate
from . import current
from . import output
from . import diff
from . import check
from . import apply


def run_async(fn):
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(fn(*args, **kwargs))
        finally:
            loop.close()

    return wrap


@click.group()
def main():
    "Manage runtime configuration for Firefox CI"


@main.command(name="generate")
@generate.options
@output.options
@run_async
@with_aiohttp_session
async def generateCommand(**kwargs):
    "Generate the the expected runtime configuration"
    output.display_resources(await generate.resources())


@main.command(name="current")
@generate.options
@output.options
@run_async
@with_aiohttp_session
async def currentCommand(**kwargs):
    "Fetch the current runtime configuration"
    # generate the expected resources so that we can limit the current
    # resources to only what we manage
    expected = await generate.resources()
    output.display_resources(await current.resources(expected.managed))


@main.command(name="diff")
@generate.options
@diff.options
@run_async
@with_aiohttp_session
async def diffCommand(**kwargs):
    "Compare the the current and expected runtime configuration"
    expected = await generate.resources()
    actual = await current.resources(expected.managed)
    different = diff.show_diff(expected, actual)
    if different:
        sys.exit(1)


@main.command(name="check")
@generate.options
@check.options
@run_async
@with_aiohttp_session
async def checkCommand(**kwargs):
    """Check the current and generated resource sets against expectations

    This uses pytest under the hood, and you can supply pytest args such
    as `-x` and `-vv` after a `--`: `ci-admin check -- -x -vv`"""
    generated = await generate.resources()
    actual = await current.resources(generated.managed)
    if not check.run_checks(generated, actual):
        sys.exit(1)


@main.command(name="apply")
@generate.options
@apply.options
@run_async
@with_aiohttp_session
async def applyCommand(**kwargs):
    "Compare the the current and expected runtime configuration"
    expected = await generate.resources()
    actual = await current.resources(expected.managed)
    await apply.apply_changes(expected, actual)


if __name__ == "__main__":
    main()
