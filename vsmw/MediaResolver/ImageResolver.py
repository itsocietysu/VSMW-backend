from io import BytesIO

from skimage import io
from skimage.transform import rescale

from vsmw.MediaResolver.MediaResolver import MediaResolver

import uuid

MAX_IMAGE_SIDE = 1024
MIN_IMAGE_SIDE = 256
MAX_ASPECT_RATIO = 1.34

class ImageResolver(MediaResolver):
    def __init__(self, _type, data):
        super().__init__(data)

        type_mapping = {
            'image': (1024, 256, 1.34),
            'equipment': (512, 32, 1.34),
        }

        self.max_image_size, self.min_image_size, self.max_aspect_ratio = \
            type_mapping[_type] \
                if _type in type_mapping \
                else (MAX_IMAGE_SIDE, MIN_IMAGE_SIDE, MAX_ASPECT_RATIO)

        self.type = _type

    def Resolve(self):
        img = io.imread(BytesIO(self.data))

        w, h = img.shape[1], img.shape[0]

        aspect = max(w, h) / min(w, h)
        if aspect > self.max_aspect_ratio:
            new_t = int(min(w, h) * self.max_aspect_ratio)
            dt = int((max(w, h) - new_t) / 2)
            if min(w, h) == h:
                img = img[:, dt:(dt + new_t)]
            else:
                img = img[dt:(dt + new_t), :]

            w, h = img.shape[1], img.shape[0]


        if max(w, h) > self.max_image_size:
            ds = self.max_image_size / max(w, h)
            img = rescale(image=img, scale=ds)

        if min(w, h) < self.min_image_size:
            raise Exception("images size too small, minimum side size = %i" % self.min_image_size)

        self.url = './images/%s.jpg' % uuid.uuid4().hex
        io.imsave(self.url, img[:, :, :3])
        return self.url
