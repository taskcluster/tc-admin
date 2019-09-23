# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import os
import click

from .appconfig import AppConfig
from .options import with_options, check_options


check_options.add(click.argument("pytest_options", nargs=-1))


@with_options("pytest_options")
def run_checks(pytest_options):
    check_path = AppConfig.current().check_path
    if not os.path.exists(check_path):
        print("No checks defined; path {} does not exist".format(check_path))
        return False
    os.chdir(check_path)
    return 0 == pytest.main(list(pytest_options))
