# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os

from tcadmin.main import main
from tcadmin.appconfig import AppConfig

from ciadmin import modify
from ciadmin.generate import (
    scm_group_roles,
    in_tree_actions,
    cron_tasks,
    hg_pushes,
    grants,
    worker_pools,
)


def boot():
    appconfig = AppConfig()

    appconfig.options.add(
        "--environment",
        required=True,
        help="environment for which resources are to be generated",
    )

    appconfig.options.add(
        "--ci-configuration-repository",
        default="https://hg.mozilla.org/ci/ci-configuration",
        help="repository containing ci-configuration",
    )

    appconfig.options.add(
        "--ci-configuration-revision",
        default="default",
        help="revision of the ci-configuration repository",
    )

    appconfig.options.add(
        "--ci-configuration-directory",
        help="local directory containing ci-configuration repository (overrides repository/revision)",
    )

    appconfig.check_path = os.path.join(os.path.dirname(__file__), "check")

    appconfig.generators.register(scm_group_roles.update_resources)
    appconfig.generators.register(in_tree_actions.update_resources)
    appconfig.generators.register(cron_tasks.update_resources)
    appconfig.generators.register(hg_pushes.update_resources)
    appconfig.generators.register(grants.update_resources)
    appconfig.generators.register(worker_pools.update_resources)

    appconfig.modifiers.register(modify.modify_resources)

    main(appconfig)
