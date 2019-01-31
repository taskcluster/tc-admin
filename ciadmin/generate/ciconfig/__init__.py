# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import click

from ...options import decorate


def options(fn):
    return decorate(
        fn,
        click.option(
            "--ci-configuration-repository",
            default="https://hg.mozilla.org/build/ci-configuration",
            help="repository containing ci-configuration",
        ),
        click.option(
            "--ci-configuration-revision",
            default="default",
            help="revision of the ci-configuration repository",
        ),
        click.option(
            "--ci-configuration-directory",
            help="local directory containing ci-configuration repository (overrides repository/revision)",
        ),
    )
