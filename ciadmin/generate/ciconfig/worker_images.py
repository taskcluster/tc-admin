# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


@attr.s(frozen=True)
class WorkerImage:
    image_name = attr.ib(type=str)
    alias_for = attr.ib(type=str, default=None)
    clouds = attr.ib(type=dict, default={})

    @staticmethod
    async def fetch_all():
        """Load worker-image metadata from worker-images.yml in ci-configuration, returning a WorkerImages
        instance that will resolve aliases."""
        worker_images = await get_ciconfig_file("worker-images.yml")

        def mk(image_name, info):
            if type(info) == str:
                return WorkerImage(image_name=image_name, alias_for=info)
            else:
                return WorkerImage(image_name=image_name, clouds=info)

        return WorkerImages(
            [mk(image_name, info) for image_name, info in worker_images.items()]
        )

    def image_id(self, cloud, *keys):
        """Look up an image_id using the keys under the given cloud for this worker image"""
        v = self.clouds[cloud]
        for k in keys:
            v = v[k]
        return v


class WorkerImages:
    def __init__(self, images):
        self.images = {i.image_name: i for i in images}

    def __getitem__(self, image_name):
        "Retrive a WorkerImage, accounting for aliases"
        while True:
            image = self.images[image_name]
            if not image.alias_for:
                return image
            image_name = image.alias_for

    def get(self, image_name, default=None):
        try:
            return self[image_name]
        except KeyError:
            return default
