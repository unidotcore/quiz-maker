import sys
from os import path, mkdir
from enum import Enum, unique
from PIL import Image, ImageOps, ImageDraw

@unique
class Position(Enum):

    TOP = 1
    CENTER = 2
    BOTTOM = 3


class Rect():

    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def __eq__(self, obj):
        return isinstance(obj, Rect) and \
        [self.left, self.top, self.right, self.bottom] == [obj.left, obj.top, obj.right, obj.bottom]

    def __ne__(self, obj):
        return not self == obj


class Maker():

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BGSIZE = (1440, 2898)

    def __init__(self, file):
        if not path.exists(file):
            raise FileExistsError('Unable to find image file at: %s' % path)
        self.basedir = path.dirname(file)
        self.filename, self.extension = path.splitext(path.basename(file))
        self.size = self.BGSIZE
        default_size = (input('[%s] Continue with default background size [W: %d, H: %d]? [y/n]: ' % \
            ((self.filename,) + self.size)).strip().lower() or 'y') == 'y'
        if not default_size:
            width = int(input('[%s] Enter new width: ' % self.filename))
            height = int(input('[%s] Enter new height: ' % self.filename))
            self.size = (width, height)
        print('[%s] Selected background size: [W: %d, H: %d]' % ((self.filename,) + self.size))
        self.dark_bg = (input('[%s] Continue with dark background? [y/n]: ' % self.filename).strip().lower() or 'y') == 'y'
        print('[%s] Selected %s background.' % (self.filename, 'dark' if self.dark_bg else 'light'))
        self.position = Position(int(input('[%s] Where would you like to paste the image? [1:top/2:center/3:bottom]: ' % \
            self.filename).strip() or Position.BOTTOM.value))
        print('[%s] Selected %s position.' % (self.filename, self.position.name.lower()))
        self.background = Image.new('RGB', self.size, self.BLACK if self.dark_bg else self.WHITE)
        self.background_rect = Rect(0, 0, *self.background.size)
        self.image = Image.open(file)
        self.image_rect = Rect(0, 0, *self.image.size)
        self.padding = self.get_padding()
        print('[%s] Loaded: [W: %d, H: %d]' % (self.filename, self.image_rect.right, self.image_rect.bottom))

    def make(self):
        resized, resized_rect = self.resize()
        is_resized = not resized is None and self.image_rect != resized_rect
        image = resized if is_resized else self.image
        rect = resized_rect if is_resized else self.image_rect
        radius = int(input('[%s] Enter corners radius [50]: ' % self.filename) or 50)
        corners_mask = self.get_corners_mask(rect, radius)
        self.background.paste(image, self.get_position(rect), corners_mask)
        corners_mask.close()
        if not resized is None:
            resized.close()

    def resize(self):
        safe_width = self.background_rect.right - self.padding.left - self.padding.right
        if self.image_rect.right == safe_width:
            return None, None
        width_ratio = (safe_width / float(self.image_rect.right))
        safe_height = int(float(self.image_rect.bottom) * float(width_ratio))
        resized = self.image.resize((safe_width, safe_height), Image.LANCZOS)
        resized_rect = Rect(0, 0, *resized.size)
        print('[%s] Image has been resized: [W: %d, H: %d]' % (self.filename, resized_rect.right, resized_rect.bottom))
        return resized, resized_rect

    def get_padding(self):
        left = int(self.background_rect.right * .0425)
        top = int(self.background_rect.bottom * .15)
        right = int(self.background_rect.right * .0425)
        bottom = int(self.background_rect.bottom * .085) # Original: .125
        print('[%s] Padding: [L: %d, T: %d, R: %d, B: %d]' % (self.filename, left, top, right, bottom))
        return Rect(left, top, right, bottom)

    def get_position(self, rect):
        x = self.padding.left
        if self.position == Position.TOP:
            y = self.padding.top
        elif self.position == Position.CENTER:
            y = (self.background_rect.bottom // 2) - (rect.bottom // 2)
        else:
            y = self.background_rect.bottom - self.padding.bottom - rect.bottom
        return (x, y)

    def get_corners_mask(self, rect, radius, fill=255):
        circle = Image.new('L', (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2), fill)
        alpha = Image.new('L', (rect.right, rect.bottom), fill)
        alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
        alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, rect.bottom - radius))
        alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (rect.right - radius, 0))
        alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (rect.right - radius, rect.bottom - radius))
        return alpha
    
    def export(self):
        output = path.join(self.basedir, '%s-story.png' % self.filename)
        self.background.save(output, quality=100)

    def close(self):
        self.background.close()
        self.image.close()
        print("[%s] Released." % self.filename)


if __name__ == "__main__":
    for file in sys.argv[1:]:
        maker = Maker(file)
        maker.make()
        maker.export()
        maker.close()