# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster import optionsFromEnvironment as originalOptions
import os


def optionsFromEnvironment():
    """Build Taskcluster options, supporting proxy"""
    if "TASKCLUSTER_PROXY_URL" in os.environ:
        return {"rootUrl": os.environ["TASKCLUSTER_PROXY_URL"]}
    else:
        return originalOptions()
