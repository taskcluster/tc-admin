# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import functools
import click
import asyncio
import sys
import os

from .util.sessions import with_aiohttp_session
from .appconfig import AppConfig
from . import current
from . import generate
from . import output
from . import diff
from . import check
from . import apply
from . import options


def pre_apply_check():
    if not os.environ.get("TASKCLUSTER_PROXY_URL"):
        if not os.environ.get("TASKCLUSTER_CLIENT_ID"):
            raise click.UsageError("TASKCLUSTER_CLIENT_ID must be set")
        if not os.environ.get("TASKCLUSTER_ACCESS_TOKEN"):
            raise click.UsageError("TASKCLUSTER_ACCESS_TOKEN must be set")


pre_cmd_checks = {
    "apply": [pre_apply_check],
}


def run_pre_check(name):
    for check_fn in pre_cmd_checks.get(name, []):
        check_fn()


def run_async(fn):
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(fn(*args, **kwargs))
        finally:
            loop.close()

    return wrap


def main(appconfig):
    @click.group()
    def cmd():
        """Manage Taskcluster configuration.

        The root URL for the Taskcluster deployment against which to run is
        given either in `tc-admin.py` or via the environment variable
        TASKCLUSTER_ROOT_URL.

        For `tcadmin apply`, TASKCLUSTER_CLIENT_ID and TASKCLUSTER_ACCESS_TOKEN
        must also be supplied.
        """
        pass

    @cmd.command(name="generate")
    @options.generate_options.apply
    @options.output_options.apply
    @appconfig.options._apply
    @run_async
    @with_aiohttp_session
    async def generateCommand(**kwargs):
        "Generate the the expected runtime configuration"
        run_pre_check("generate")
        with AppConfig._as_current(appconfig):
            output.display_resources(await generate.resources())

    @cmd.command(name="current")
    @options.generate_options.apply
    @options.output_options.apply
    @appconfig.options._apply
    @run_async
    @with_aiohttp_session
    async def currentCommand(**kwargs):
        "Fetch the current runtime configuration"
        # generate the expected resources so that we can limit the current
        # resources to only what we manage
        run_pre_check("current")
        with AppConfig._as_current(appconfig):
            expected = await generate.resources()
            output.display_resources(await current.resources(expected.managed))

    @cmd.command(name="diff")
    @options.generate_options.apply
    @options.diff_options.apply
    @appconfig.options._apply
    @run_async
    @with_aiohttp_session
    async def diffCommand(**kwargs):
        "Compare the the current and expected runtime configuration"
        run_pre_check("diff")
        with AppConfig._as_current(appconfig):
            expected = await generate.resources()
            actual = await current.resources(expected.managed)
            different = diff.show_diff(expected, actual)
            if different:
                sys.exit(2)

    @cmd.command(name="check")
    @options.generate_options.apply
    @options.check_options.apply
    @appconfig.options._apply
    def checkCommand(**kwargs):
        """Check the current and generated resource sets against expectations

        This uses pytest under the hood, and you can supply pytest args such
        as `-x` and `-vv` after a `--`: `ci-admin check -- -x -vv`"""
        run_pre_check("check")
        with AppConfig._as_current(appconfig):
            if not check.run_checks():
                sys.exit(1)

    @cmd.command(name="apply")
    @options.generate_options.apply
    @options.diff_options.apply
    @appconfig.options._apply
    @run_async
    @with_aiohttp_session
    async def applyCommand(**kwargs):
        "Apply the expected runtime configuration"
        run_pre_check("apply")

        with AppConfig._as_current(appconfig):
            expected = await generate.resources()
            actual = await current.resources(expected.managed)
            await apply.apply_changes(expected, actual)

    cmd()
