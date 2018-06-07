from setuptools import setup, find_packages

setup(name='ci-admin',
      version='1.0.0',
      description='Administration of runtime configuration (Taskcluster settings) for Firefox CI',
      author=u'Dustin Mitchell',
      author_email='dustin@mozilla.com',
      url='https://hg.mozilla.org/build/ci-admin',
      packages=find_packages('.'),
      install_requires=[
          'taskcluster',
          'click',
          'blessings',
          'attrs',
          'memoized',
          'sortedcontainers',
          'aiohttp',
          'pyyaml',
          'iso8601',
          'json-e',
      ],
      setup_requires=[
          'pytest-runner',
          'flake8',
      ],
      tests_require=[
          'pytest',
          'pytest-mock',
          'pytest-asyncio',
          'flake8',
      ],
      classifiers=(
          "Programming Language :: Python :: 3",
      ),
      entry_points={
          'console_scripts': [
              'ci-admin = ciadmin.main:main',
          ]
      })
