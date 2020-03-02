from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name="tc-admin",
    version="2.4.0",
    description="Administration of Taskcluster runtime configuration",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dustin Mitchell",
    author_email="dustin@mozilla.com",
    url="https://github.com/taskcluster/tc-admin",
    packages=find_packages("."),
    install_requires=[
        "taskcluster~=25.4.0",
        "click~=7.0",
        "blessings~=1.7",
        "attrs~=19.3.0",
        "memoized==0.3",  # no semver..
        "sortedcontainers~=2.1.0",
        "aiohttp~=2.3.10",
        "pytest~=5.2",
        "pyyaml~=4.2b1",
        "patiencediff==0.1.0",
    ],
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest", "pytest-mock", "pytest-asyncio~=0.10.0", "flake8"],
    classifiers=("Programming Language :: Python :: 3",),
    entry_points={
        "console_scripts": [
            "tc-admin = tcadmin.boot:boot",
        ]},
)
