from setuptools import setup, find_packages

setup(
    name="ci-admin",
    version="1.0.0",
    description="Administration of runtime configuration (Taskcluster settings) for Firefox CI",
    author=u"Dustin Mitchell",
    author_email="dustin@mozilla.com",
    url="https://hg.mozilla.org/build/ci-admin",
    packages=find_packages("."),
    install_requires=[
        "taskcluster<5",
        "click<7",
        "blessings<2",
        "attrs",  # http://www.attrs.org/en/stable/backward-compatibility.html
        "memoized==0.3",  # no semver..
        "sortedcontainers<3",
        "aiohttp<3",
        "pyyaml<4",
        "iso8601==0.1.12",  # no semver..
        "json-e<3",
        "pytest<4",
    ],
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest-mock", "pytest-asyncio", "flake8"],
    classifiers=("Programming Language :: Python :: 3",),
    entry_points={"console_scripts": ["ci-admin = ciadmin.main:main"]},
)
