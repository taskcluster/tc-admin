# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.generate.ciconfig.worker_images import WorkerImage, WorkerImages


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file("worker-images.yml", {})
    assert (await WorkerImage.fetch_all()).images == {}


@pytest.mark.asyncio
async def test_fetch_entry(mock_ciconfig_file):
    mock_ciconfig_file(
        "worker-images.yml", {"lazy-worker": {"ec2": {"aa-polar-1": "ami-123"}}}
    )
    assert (await WorkerImage.fetch_all())["lazy-worker"] == WorkerImage(
        image_name="lazy-worker",
        alias_for=None,
        clouds={"ec2": {"aa-polar-1": "ami-123"}},
    )


@pytest.mark.asyncio
async def test_fetch_alias_entry(mock_ciconfig_file):
    mock_ciconfig_file(
        "worker-images.yml",
        {
            "copy-worker": "lazy-worker",
            "lazy-worker": {"ec2": {"aa-polar-1": "ami-123"}},
        },
    )
    assert (await WorkerImage.fetch_all())["copy-worker"] == WorkerImage(
        image_name="lazy-worker", clouds={"ec2": {"aa-polar-1": "ami-123"}}
    )


def test_worker_image_image_id():
    img = WorkerImage("img", clouds={"ec2": {"aa-polar-1": "ami-123"}})
    assert img.image_id("ec2", "aa-polar-1") == "ami-123"


def test_worker_images_get():
    imgs = WorkerImages(
        [
            WorkerImage("image-1", alias_for="image-2"),
            WorkerImage("image-2", clouds={"packet": {}}),
        ]
    )
    assert imgs["image-1"].clouds == {"packet": {}}
    assert imgs.get("image-2").clouds == {"packet": {}}
    assert imgs["image-1"].clouds == {"packet": {}}
    assert imgs.get("image-2").clouds == {"packet": {}}
    assert imgs.get("image-3") is None
