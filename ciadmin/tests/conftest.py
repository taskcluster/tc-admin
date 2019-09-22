# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from ciadmin.generate.ciconfig import get


@pytest.fixture
def mock_ciconfig_file(mocker):
    """
    Set a mock value for `get_ciconfig_file`.
    """

    def mocker(filename, content):
        get._cache[filename] = content

    yield mocker
    get._cache.clear()
