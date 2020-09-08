# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re


class Resolver:
    """
    A scope expander, to emulate the expansion performed by the Taskcluster
    Auth service.
    """

    def __init__(self, roles):
        "Instantiate given roles of the form {roleId: [scopes]}"
        self.roles = roles

    @classmethod
    def from_resources(cls, resources):
        """Construct an instance from a Resources instance, ignoring any non-Role
        resources"""
        from ..resources import Role

        roles = {}
        for resource in resources:
            if isinstance(resource, Role):
                roles[resource.roleId] = resource.scopes[:]
        return cls(roles)

    def _star_match(self, star_match, role_scopes):
        if star_match.endswith("*"):
            pat = re.compile(
                r"<\.\.>.*"
            )  # * in star_match consumes everything after <...>
        else:
            pat = re.compile(r"<\.\.>")
        scopes = set()
        for rs in role_scopes:
            scopes.add(pat.sub(star_match, rs))
        return scopes

    def expandScopes(self, scopes):
        """
        Given a set of scopes, expand them, following the same rules that the
        taskcluster-auth service does.  But not the same algorithm -- this is
        potentially *very* slow.
        """
        assert isinstance(scopes, list)
        scopes = {s: set() for s in scopes}
        expanded = set()

        def add_scope(scope, for_role):
            scopes.setdefault(scope, set()).add(for_role)

        for _ in range(100):
            prev = scopes.copy()

            for scope, already_expanded in prev.items():
                if scope in expanded:
                    continue
                expanded.add(scope)

                for role, role_scopes in self.roles.items():
                    assume = "assume:{}".format(role)
                    if role.endswith("*"):
                        pfx = assume[:-1]
                        if scope.startswith(pfx):
                            for s in self._star_match(scope[len(pfx):], role_scopes):
                                add_scope(s, role)
                                scopes[s].update(already_expanded)
                    if scope.endswith("*"):
                        pfx = scope[:-1]
                        if assume.startswith(pfx):
                            if assume.endswith("*"):
                                for s in self._star_match("*", role_scopes):
                                    add_scope(s, role)
                                    scopes[s].update(already_expanded)
                            else:
                                for s in role_scopes:
                                    add_scope(s, role)
                                    scopes[s].update(already_expanded)
                    if scope == assume:
                        for s in role_scopes:
                            add_scope(s, role)
                            scopes[s].update(already_expanded)

            if scopes == prev:
                break
        else:
            raise RuntimeError("maxium role expansion depth reached")

        return normalizeScopes(scopes)


def satisfies(have, require):
    """Return True if the scopes in "have" satisfy the scopes in "require".
    """
    assert isinstance(have, list)
    assert isinstance(require, list)
    for req_scope in require:
        for have_scope in have:
            if have_scope == req_scope or (
                have_scope.endswith("*") and req_scope.startswith(have_scope[:-1])
            ):
                break
        else:
            return False
    return True


def normalizeScopes(scopes):
    """Return a "normalized" version of the given scopes, such that no scope
    satisfies any other.  """
    # this is O(n^2) but we don't manage 1000's of scopes, so it's OK for now
    scopes = set(scopes)  # remove duplicates
    scopes = sorted(
        p1
        for p1 in scopes
        if all(
            p1 == p2 or not (p2.endswith("*") and p1.startswith(p2[:-1]))
            for p2 in scopes
        )
    )
    return scopes
