# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from tcadmin.util.matchlist import MatchList


def test_MatchList_iter():
    ml = MatchList(["a.*", "b$", "abc$"])
    assert list(ml) == ["a.*", "b$", "abc$"]


def test_MatchList_matches_exact():
    ml = MatchList(["a.*", "b"])
    assert ml.matches("b")
    assert not ml.matches("x")


def test_MatchList_matches_longer_star():
    ml = MatchList(["a[bcx-z]+", "b$", "abc$"])
    assert ml.matches("abc")
    assert ml.matches("axyz")


def test_MatchList_match_rooted():
    ml = MatchList(["ab+"])
    assert ml.matches("abc")
    assert not ml.matches("xabc")
