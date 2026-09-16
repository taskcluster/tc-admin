# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from tcadmin.util.matchlist import MatchList


def test_MatchList_iter():
    ml = MatchList(["a.*", "b$", "abc$"])
    assert [entry.include for entry in ml] == ["a.*", "b$", "abc$"]


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


def test_MatchList_add_with_excludes():
    "A pattern's excludes carve out sub-matches from that pattern only"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*"])
    assert ml.matches("ax")
    assert not ml.matches("abx")


def test_MatchList_excludes_are_scoped_to_their_own_pattern():
    "An exclude on one pattern must not suppress a match from another pattern"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*"])
    ml.add("ab.*")
    assert ml.matches("abx")


def test_MatchList_iter_yields_entries_with_excludes():
    "Iterating a MatchList exposes each entry's excludes, not just its pattern"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*"])
    (entry,) = list(ml)
    assert entry.include == "a.*"
    assert list(entry.excludes) == ["ab.*"]


def test_MatchList_extend():
    "extend folds another MatchList's patterns (and their excludes) in"
    a = MatchList([])
    a.add("a.*", excludes=["ab.*"])
    b = MatchList([])
    b.add("ab.*")

    a.extend(b)

    assert [entry.include for entry in a] == ["a.*", "ab.*"]
    assert a.matches("ax")
    assert a.matches("abx")


def test_MatchList_to_json_without_excludes():
    "A pattern with no excludes serializes as a bare string"
    ml = MatchList([])
    ml.add("a.*")
    assert ml.to_json() == ["a.*"]


def test_MatchList_to_json_with_excludes():
    "A pattern with excludes serializes as a dict"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*"])
    assert ml.to_json() == [{"include": "a.*", "excludes": ["ab.*"]}]


def test_MatchList_from_json_round_trip():
    "from_json reconstructs excludes lost by plain __iter__"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*"])

    round_tripped = MatchList(ml.to_json())

    assert round_tripped.matches("ax")
    assert not round_tripped.matches("abx")


def test_MatchList_str_without_excludes():
    "A pattern with no excludes is displayed as a bare bullet"
    ml = MatchList([])
    ml.add("a.*")
    assert str(ml) == "- a.*"


def test_MatchList_str_with_excludes():
    "A pattern's excludes are shown one per line, indented under it"
    ml = MatchList([])
    ml.add("a.*", excludes=["ab.*", "ac.*"])
    assert str(ml) == "- a.*\n  Excluding:\n    - ab.*\n    - ac.*"
