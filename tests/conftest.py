# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest


@pytest.fixture
def ciconfig_get(mocker):
    '''
    Mock out ciconfig.get (which would ordinarily fetch something remotely).

    The expected return value should be set in ciconfig_get.fake_values[filename]
    '''
    get = mocker.patch('ciadmin.generate.ciconfig.get')
    fake_values = {}

    async def fake_get(filename):
        return fake_values[filename]
    get.side_effect = fake_get
    get.fake_values = fake_values
    return get


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
