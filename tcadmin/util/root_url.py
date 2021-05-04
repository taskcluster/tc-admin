# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os
import click

from ..appconfig import AppConfig


_root_url = None


async def root_url():
    """Helper function to get the root URL"""
    global _root_url
    if _root_url:
        return _root_url

    appconfig = AppConfig.current()
    if appconfig.root_url:
        root_url = appconfig.root_url
        if callable(root_url):
            root_url = await appconfig.root_url()
        if "TASKCLUSTER_ROOT_URL" in os.environ:
            if os.environ["TASKCLUSTER_ROOT_URL"] != root_url:
                raise click.UsageError(f"TASKCLUSTER_ROOT_URL does not match {root_url}")
        _root_url = root_url
    else:
        if "TASKCLUSTER_ROOT_URL" not in os.environ:
            raise click.UsageError("TASKCLUSTER_ROOT_URL must be set")
        _root_url = os.environ["TASKCLUSTER_ROOT_URL"]
    return _root_url
