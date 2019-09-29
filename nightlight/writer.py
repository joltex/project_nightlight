import board
import json
from nightlight import adafruit_dotstar
import logging

DEFAULT_RESOLUTION = (30, 18)


def main():
    """
    Commandline entrypoint -
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to a nightlight file or directory of nightlight files.')
    patterns = load_nightlight_files(nighlights_paths)
    board = Nightlight()
    start_the_show(board, patterns)

def get_file_paths(path, valid_extensions=None):
    if valid_extensions is None:
        valid_extensions = [""]

    if isinstance(path, str) and os.path.isdir(path):
        files = [os.path.join(path, x)
                  for x in os.listdir(path)
                  if x.endswith(tuple(valid_extensions))]

    elif isinstance(path, str) and os.path.exists(path):
        files = [path] if path.endswith(tuple(valid_extensions)) else []
    else:
        raise TypeError('Input must be either a video file or a directory of video files')
    if not files:
        raise ValueError('Input does not include any video files with recognized extensions'
                         ' ({})'.format(valid_extensions))
    return files


def load_nightlight_files(path):
    paths = get_file_paths(path)
    result = []
    for file_path in paths:
        try:
            result.append(json.load(file_path))
        except:
            logging.error("Could not load nightlight file %r", path)
    return result


def start_the_show(patterns, board):
    while 1:
        for pattern in patterns:
            board.write_pattern(pattern)

class Nightlight:

    def __init__(self, resolution=DEFAULT_RESOLUTION, clock_pin=board.SCK, data_pin=board.MOSI,
                 baudrate=4000000):
        self._width = resolution[0]
        self._height = resolution[1]
        self._board = adafruit_dotstar.DotStar(
            clock_pin,
            data_pin,
            n=self._width * self._height,
            baudrate=baudrate)

    def write_pattern(self, pattern):
        """ Write a nightlight pattern to the board.

        :param pattern: Nighlight pattern to write to the board
        """
        for y, row in enumerate(pattern):
            for x, pixel in enumerate(row):
                self._write_pixel(x, y, pixel)

    def _write_pixel(self, x, y, colour):
        """ Write a single pixel to its x, and y coordinate.

        Since the board is wired_up in an "S" pattern, every odd row goes in the opposite
        direction:
           > > > > > > ↓
         ↓ < < < < < <
           > > > > > > ↓
              ...

        :param x: `x` coordinate of pixel to write
        :param y: `y` coordinate of pixel to write
        :param colour: RGB tuple of colour to write
        """
        if not y % 2:
            x = self._width - x
        pixel_number = y * self._height + x
        self._board[pixel_number] = tuple(colour)

    def _write_colour(self, colour):
        """ Write a single colour to the whole board

        :param colour: RGB colour to write to the board.
        """
        self._board.fill(colour)

