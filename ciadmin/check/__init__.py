# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import os
import click

from ..options import decorate, with_click_options


def options(fn):
    return decorate(fn, click.argument("pytest_options", nargs=-1))


@with_click_options("pytest_options")
def run_checks(generated_, actual_, pytest_options):
    global generated, actual
    generated = generated_
    actual = actual_
    return 0 == pytest.main([os.path.dirname(__file__) + "/"] + list(pytest_options))
