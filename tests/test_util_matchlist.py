# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.util.matchlist import MatchList


@pytest.fixture
def minimize():
    return lambda patterns: sorted(MatchList(patterns))


def test_MatchList_empty_string():
    with pytest.raises(
        RuntimeError, message="Empty strings are not alloewd in MatchList"
    ):
        MatchList([""])


def test_MatchList_minimize_empty(minimize):
    assert minimize([]) == []


def test_MatchList_minimize_single(minimize):
    assert minimize(["abc*"]) == ["abc*"]


def test_MatchList_minimize_duplicate(minimize):
    "a pattern that appears twice is reduced to just one"
    assert minimize(["abc*", "abc*"]) == ["abc*"]


def test_MatchList_minimize_longer(minimize):
    'a starred pattern "consumes" longer patterns"'
    assert minimize(["a*", "abc*", "abd", "abcdiary", "abelincoln"]) == ["a*"]


def test_MatchList_minimize_with_common_prefix(minimize):
    "A pattern that is just a prefix of another does not consume anything"
    assert minimize(["a", "abc*", "abd", "abelincoln"]) == [
        "a",
        "abc*",
        "abd",
        "abelincoln",
    ]


def test_MatchList_add():
    "Patterns stay minimal while adding elements one at a time"
    ml = MatchList(["a*", "b"])
    assert sorted(ml) == ["a*", "b"]
    ml.add("abc")
    assert sorted(ml) == ["a*", "b"]
    ml.add("bdef")
    assert sorted(ml) == ["a*", "b", "bdef"]
    ml.add("b*")
    assert sorted(ml) == ["a*", "b*"]


def test_MatchList_matches_exact():
    ml = MatchList(["a*", "b"])
    assert ml.matches("b")
    assert not ml.matches("x")


def test_MatchList_matches_exact_star():
    ml = MatchList(["a*", "b", "abc"])
    assert ml.matches("a*")
    assert not ml.matches("bbc")


def test_MatchList_matches_longer_star():
    ml = MatchList(["a*", "b", "abc"])
    assert ml.matches("abc")
    assert ml.matches("axyz")
