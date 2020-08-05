# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-slow", action="store_true", default=False, help="skip slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-slow"):
        skip_slow = pytest.mark.skip(reason="skipping slow tests")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="module")
def appconfig():
    # don't import this at the top level, as it results in `blessings.Terminal` being
    # initialized in a situation where output is to a console, and it includes underlines
    # and bold and colors in the output, causing test failures
    from tcadmin.appconfig import AppConfig

    appconfig = AppConfig()
    with AppConfig._as_current(appconfig):
        yield appconfig
