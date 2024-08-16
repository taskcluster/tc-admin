# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import click

from .options import with_options, output_options


output_options.add(click.option("--yaml/--json", default=True, help="output format"))
output_options.add(
    click.option("--grep", help="regular expression limiting resources displayed")
)


@with_options("yaml", "grep")
def display_resources(resources, yaml, grep):
    if grep:
        resources = resources.filter(grep)
    if yaml:
        print(resources.to_yaml())
    else:
        print(resources.to_json())
