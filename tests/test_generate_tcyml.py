# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os.path
import attr
import pytest
import hashlib

from ciadmin.util.sessions import with_aiohttp_session
from ciadmin.generate import tcyml

# pin a revision of mozilla-central so we know what to expect
PINNED_REV = 'ff8505d177b9'

@pytest.mark.asyncio
@with_aiohttp_session
async def test_get_tcyml():
    res = await tcyml.get('https://hg.mozilla.org/mozilla-central', revision=PINNED_REV)
    assert hashlib.sha512(res).hexdigest()[:10] == '684648599a'
