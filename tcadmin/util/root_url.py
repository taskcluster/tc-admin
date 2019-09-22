# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os


def root_url():
    """Helper function to get the root URL"""
    return os.environ["TASKCLUSTER_ROOT_URL"]
