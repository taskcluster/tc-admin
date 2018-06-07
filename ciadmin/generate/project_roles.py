# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import textwrap

from ..resources import Role
from .projects import Project


async def update_resources(resources):
    '''

    Manage the roles for various projects.  This is a tree of roles designed to
    minimize unnecessary repetition of scopes; it is designed as follows:

    - 'repo:<repo>:*' -- scopes for anything to do with the project's repo
      has 'assume:<roleRoot>:branch:<domain>:level-<level>:<alias>'
      has 'assume:<roleRoot>:feature:<feature>:<domain>:level-<level>:<alias>
        for each feature associated with the project (omitting some unecessary
        features)
      has any extra scopes associated with the project

    - 'repo:<repo>:branch:default' -- scopes for pushes to the project's repo
      has 'assume:<roleRoot>:branch:<domain>:level-<level>:<alias>'

    - 'repo:<repo>:cron:nightly-*' -- scopes for nightlies (if configured)
      has 'assume:<roleRoot>:nightly:level-<level>:<alias>'

    Those are implemented with a number of parameterized roles where the '*'
    matches the alias. In effect, this is how we translate from a repository
    path to an alias.

    - '<roleRoot>:branch:<domain>:level-<level>:*' -- scopes for the branch as a whole
      has 'assume:moz-tree:level:<level>:<domain>', which provides most of the scopes
      has project-specific route scopes

    - '<roleRoot>:push:<domain>:level-<level>:*' -- scopes for pushes
      has 'in-tree:hook-action:project-<domain>/in-tree-action-<level>-*' which allows
        actions to run against pushes

    - '<roleRoot>:feature:<feature>:<domain>:level-<level>:*' -- scopes for features
      these depend on the specific feature; see below

    - '<roleRoot>:nightly:level-<level>:*-- scopes for nightly releases
      (these are still manually maintained)

    In all of this, <roleRoot> is a string that differs depending on the trust domain
    and will likely change soon.
    '''
    # features for which we need roles; this is checked against features for which we create roles
    feature_roles = set([
        'taskcluster-docker-routes-v1',
        'taskcluster-docker-routes-v2',
        'buildbot',
        'is-trunk',
    ])

    role_roots = {
        'gecko': 'project:releng',
        'comm': 'project:comm:thunderbird:comm:releng',
    }

    for root in role_roots.values():
        resources.manage('Role={}:branch:*'.format(root))
        resources.manage('Role={}:push:*'.format(root))
        resources.manage('Role={}:feature:*'.format(root))
        # nightly are still manually maintained

    projects = await Project.fetch_all()

    for project in projects:
        subs = {}
        subs['domain'] = domain = project.trust_domain
        subs['role_root'] = role_roots[domain]
        subs['level'] = project.level
        subs['alias'] = project.alias

        repo_prefix = 'repo:hg.mozilla.org/{}'.format(project.hgmo_path)
        resources.manage('Role={}:*'.format(repo_prefix))

        # repo:<repo>:*
        resources.add(Role(
            roleId=repo_prefix + ':*',
            description='Scopes that apply to everything occuring in this repository - push, cron, actions, etc.',
            scopes=[
                'assume:{role_root}:branch:{domain}:level-{level}:{alias}'.format(**subs),
            ] + [
                'assume:{role_root}:feature:{feature}:{domain}:level-{level}:{alias}'.format(
                    feature=feature, **subs)
                for feature in project.enabled_features
                if feature in feature_roles
            ] + project.extra_tc_scopes))

        # repo:<repo>:branch:default
        resources.add(Role(
            roleId=repo_prefix + ':branch:default',
            description='Scopes that apply to pushes to this repository only (not actions or crontasks)',
            scopes=[
                'assume:{role_root}:push:{domain}:level-{level}:{alias}'.format(**subs),
            ]))

        # repo:<repo>:cron:nightly-* (only if cron runs on this project)
        if project.feature('taskcluster-cron'):
            resources.add(Role(
                roleId=repo_prefix + ':cron:nightly-*',
                description='Scopes that apply to nightly releases from this repository',
                scopes=[
                    'assume:{role_root}:nightly:level-{level}:{alias}'.format(**subs),
                ]))

    all_domains = set(p.trust_domain for p in projects)
    all_levels = set(p.level for p in projects)
    for domain in all_domains:
        for level in all_levels:
            subs = {'domain': domain, 'level': level, 'role_root': role_roots[domain]}

            # <role_root>:branch:..
            resources.add(Role(
                roleId='{role_root}:branch:{domain}:level-{level}:*'.format(**subs),
                description=textwrap.dedent("""\
                    Scopes for tasks associated with all {domain} projects at level {level};
                    the '*' matches the project name.""").format(**subs),
                scopes=[s.format(**subs) for s in [
                    # most of the interesting scopes are in moz-tree:level:<level>:<domain>, which
                    # is managed by hand
                    'assume:moz-tree:level:{level}:{domain}',

                    # routes to support indexing by product
                    'queue:route:index.{domain}.v2.<..>.*',
                    'index:insert-task:{domain}.v2.<..>.*',

                    # routes to support locating tasks that create specific versions of artifacts
                    # (toolchains, etc.)
                    'queue:route:index.{domain}.cache.level-{level}.*',
                    'index:insert-task:{domain}.cache.level-{level}.*',

                    # routes to support reporting to treeherder
                    'queue:route:tc-treeherder-stage.<..>.*',
                    'queue:route:tc-treeherder.<..>.*',
                    'queue:route:tc-treeherder-stage.v2.<..>.*',
                    'queue:route:tc-treeherder.v2.<..>.*',

                    # coalescing routes support dropping unnecessary tasks under loda
                    'queue:route:coalesce.v1.builds.<..>.*',  # deprecated - bug 1382204
                    'queue:route:coalesce.v1.<..>.*',

                    'queue:route:index.releases.v1.<..>.*',
                    'index:insert-task:releases.v1.<..>.*',
                    # allow fetching secrets appropriate to this level
                    'secrets:get:project/releng/{domain}/build/level-{level}/*',
                ]]))

            # <role_root>:push:..
            resources.add(Role(
                roleId='{role_root}:push:{domain}:level-{level}:*'.format(**subs),
                description=textwrap.dedent("""\
                    Scopes for tasks associated with pushes to all {domain} projects at level {level};
                    the '*' matches the project name.""").format(**subs),
                scopes=[
                    # this scope is included in the decision task's .scopes, and indicates which in-tree
                    # action hooks may be triggered for the taskgroup. We use this to limit the actions
                    # on a taskgraph to those at the appropriate level, preventing someone with level-3
                    # access from being tricked into running a level-3 hook on a level-1 (try) push.
                    'in-tree:hook-action:project-{domain}/in-tree-action-{level}-*'.format(**subs),
                ]))

            # <role_root>:feature:..
            made_feature_roles = set()

            def makeFeature(feature, scopes):
                made_feature_roles.add(feature)
                resources.add(Role(
                    roleId='{role_root}:feature:{feature}:{domain}:level-{level}:*'.format(
                        feature=feature, **subs),
                    description=textwrap.dedent("""\
                        Scopes for tasks associated with all {domain} projects with feature {feature}
                        at level {level}; the '*' matches the project name.""").format(feature=feature, **subs),
                    scopes=scopes))

            # docker-routes v1 does not have the level in the route name, so it's deprecated
            makeFeature('taskcluster-docker-routes-v1', [
                'queue:route:index.docker.images.v1.<..>.*',
                'index:insert-task:docker.images.v1.<..>.*',
            ])

            # docker-routes v2 allows indexing of docker images, segregated per level
            makeFeature('taskcluster-docker-routes-v2', [
                'queue:route:index.docker.images.v2.level-{level}.*'.format(**subs),
            ])

            # buildbot includes scopes required for branches still using buildbot-bridge
            makeFeature('buildbot', [
                'queue:route:index.buildbot.branches.<..>.*',
                'index:insert-task:buildbot.branches.<..>.*',
                'queue:route:index.buildbot.revisions.*',
                'index:insert-task:buildbot.revisions.*',
                'project:releng:buildbot-bridge:builder-name:release-<..>-*',
                'project:releng:buildbot-bridge:builder-name:release-<..>_*',
            ])

            # trunk branches get to index under a common "trunk" path, used to find artifacts from
            # an arbitrary one of those branches
            makeFeature('is-trunk', [
                'queue:route:index.{domain}.v2.trunk.revision.*'.format(**subs),
            ])

            if made_feature_roles != feature_roles:
                raise AssertionError(
                    'made a different set of feature roles than were configured for repos; '
                    'made roles {} but expected roles {}'.format(made_feature_roles, feature_roles))
