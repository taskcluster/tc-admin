from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name="tc-admin",
    version="1.0.0",
    description="Administration of Taskcluster runtime configuration",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dustin Mitchell",
    author_email="dustin@mozilla.com",
    url="https://github.com/taskcluster/tc-admin",
    packages=find_packages("."),
    install_requires=[
        "taskcluster~=16.2.0",
        "click<7",
        "blessings<2",
        "attrs",  # http://www.attrs.org/en/stable/backward-compatibility.html
        "memoized==0.3",  # no semver..
        "sortedcontainers<3",
        "aiohttp<4",
        "pyyaml<6",
        "iso8601==0.1.12",  # no semver..
    ],
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest<4", "pytest-mock", "pytest-asyncio", "flake8"],
    classifiers=("Programming Language :: Python :: 3",),
    entry_points={
        "console_scripts": [
            "tc-admin = tcadmin.boot:boot",
        ]},
)
