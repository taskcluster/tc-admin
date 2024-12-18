from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name="tc-admin",
    version="4.0.2",
    description="Administration of Taskcluster runtime configuration",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dustin Mitchell",
    author_email="dustin@mozilla.com",
    url="https://github.com/taskcluster/tc-admin",
    packages=find_packages("."),
    install_requires=[
        "taskcluster>=44.0.0,<77.1",
        "click>=8.0.0,<8.2",
        "blessings~=1.7",
        "attrs>=21.4.0,<24.4",
        "sortedcontainers~=2.4.0",
        "aiohttp>=3.8.0,<3.12",
        "pytest>=7.0.0,<8.4",
        "pyyaml~=6.0",
    ],
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest", "pytest-mock", "pytest-asyncio>=0.18.0,<0.26", "flake8", "asyncmock"],
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        "console_scripts": [
            "tc-admin = tcadmin.boot:boot",
        ]},
)
