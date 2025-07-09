from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name="tc-admin",
    version="5.0.0",
    description="Administration of Taskcluster runtime configuration",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Dustin Mitchell",
    author_email="dustin@mozilla.com",
    url="https://github.com/taskcluster/tc-admin",
    packages=find_packages("."),
    install_requires=[
        "taskcluster>=44.0.0,<86.1",
        "click>=8.0.0,<8.3",
        "blessings~=1.7",
        "attrs>=21.4.0,<25.4",
        "sortedcontainers~=2.4.0",
        "aiohttp>=3.8.0,<3.13",
        "pytest>=7.0.0,<8.5",
        "pyyaml~=6.0",
    ],
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest", "pytest-mock", "pytest-asyncio>=0.18.0,<1.1", "flake8", "asyncmock"],
    classifiers=[
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    entry_points={
        "console_scripts": [
            "tc-admin = tcadmin.boot:boot",
        ]},
)
