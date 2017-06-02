import logging
import os
import time

from chameleon import PageTemplate
from chameleon.utils import Markup
from PIL import Image, ExifTags
from watchdog.observers import Observer

logger = logging.getLogger('main')


_sizes = {
    'thumb': (300, 300),
    'large': (1000, 1000)
}


def create_thumbnail(input_filename, output_filename, size):
    if os.path.exists(output_filename):
        return
    print(f'processing {input_filename}')
    im = Image.open(input_filename)

    if hasattr(im, '_getexif'):  # only present in JPEGs
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        e = im._getexif()  # returns None if no EXIF data
        if e is not None:
            exif = dict(e.items())
            orientation = exif[orientation]

            if orientation == 3:
                im = im.transpose(Image.ROTATE_180)
            elif orientation == 6:
                im = im.transpose(Image.ROTATE_270)
            elif orientation == 8:
                im = im.transpose(Image.ROTATE_90)

    im.thumbnail(_sizes[size], Image.ANTIALIAS)
    im.save(output_filename, "JPEG")


def render_gallery(name):
    base_path = os.path.join('images', name)

    output_base_path = os.path.join('images/build', name)
    if not os.path.exists(output_base_path):
        os.makedirs(output_base_path)

    images = []
    for filename in sorted(os.listdir(base_path), key=str.lower):
        filepath = os.path.join(base_path, filename)
        main = '.'.join(filename.split('.')[:-1])
        thumb_filepath = os.path.join(output_base_path, f'{main}-thumb.jpg')
        large_filepath = os.path.join(output_base_path, f'{main}-large.jpg')
        create_thumbnail(filepath, thumb_filepath, 'thumb')
        create_thumbnail(filepath, large_filepath, 'large')

        images.append({
            'original': filepath,
            'thumb': thumb_filepath,
            'large': large_filepath
        })

    fi = open('gallery.pt')
    txt = fi.read()
    fi.close()
    return Markup(PageTemplate(txt)(
        images=images,
        name=name
    ))


class Builder:
    def dispatch(self, *args):
        try:
            self.build()
        except:
            logger.error('Error building', exc_info=True)

    def build(self):
        fi = open('index.pt')
        data = fi.read()
        fi.close()

        template = PageTemplate(data)
        fi = open('index.html', 'w')
        fi.write(template(
            render_gallery=render_gallery
        ))
        fi.close()
        time.sleep(0.5)


if __name__ == '__main__':
    observer = Observer()
    builder = Builder()
    builder.build()
    observer.schedule(builder, '.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
