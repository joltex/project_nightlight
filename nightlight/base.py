""" base.py

This module contains the Nightlight class, which represents the actual Nightlight board and
associated methods for writing pixels and playing patterns.

"""
import time

try:
    import board
except NotImplementedError:
    # If you try to import 'board' on a PC, it will fail to detect a recognized board and raise
    # an exception. If this happens, create a mock board object so that at least the converter
    # module can be run.
    print('WARNING: No valid board (Raspberry Pi, Arduino, etc.) detected. You will not'
          ' be able to play anything.')
    from unittest.mock import Mock
    board = Mock(['SCK', 'MOSI'])

from nightlight import adafruit_dotstar


class Nightlight:

    def __init__(self, width=30, height=18, clock_pin=board.SCK, data_pin=board.MOSI,
                 baudrate=4000000, max_brightness=1.0, default_frame_rate=30):
        self._width = width
        self._height = height
        self._max_brightness = max_brightness
        self._default_frame_rate = default_frame_rate
        self._leds = adafruit_dotstar.DotStar(clock_pin, data_pin, n=(self._width * self._height),
                                              baudrate=baudrate, pixel_order=adafruit_dotstar.RGB,
                                              auto_write=False)

    def write_pattern(self, pattern, frame_rate=None):
        """ Write a pattern to the Nightlight

        :param pattern: Nightlight pattern to write.
        :param frame_rate: Frame rate in frames per second.
        """
        if frame_rate is None:
            frame_rate = self._default_frame_rate
        time_per_frame = 1.0 / frame_rate

        last_frame = time.time()
        for frame in pattern:
            for y, row in enumerate(frame):
                for x, pixel in enumerate(row):
                    self._write_pixel(x, y, pixel)
            self._leds.show()
            self._sleep_frame(last_frame, time_per_frame)
            last_frame = time.time()

    def _sleep_frame(self, last_frame, time_per_frame):
        """ Sleep between frames to write to the board at a correct frame rate.

        :param last_frame: Timestamp of when the last frame was written.
        :param time_per_frame: The total time to wait on each frame.
        """
        time_elapsed = time.time() - last_frame
        time_to_wait = time_per_frame - time_elapsed
        if time_to_wait > 0:
            time.sleep(time_to_wait)

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
        pixel = self._calculate_pixel(colour)
        self._leds[pixel_number] = pixel

    def _calculate_pixel(self, colour):
        brightness = self._calculate_brightness(colour)
        return tuple(colour) + (brightness,)

    def _calculate_brightness(self, colour):
        """ Calculate the brightness of each pixel.

        The brighness of each pixel should vary with depending on the RGB value
        of the colour.  Sending (100, 100, 100) should be a much more dim than
        what is sent by default.

        The formula used here was taken from:
        https://tinyurl.com/y9lqf5bs

        The stackoverflow comments have a few alternatives, if we need to
        switch-it-up.

        :param colour: RGB value of colour find brightness of.
        :return: Brightness of the colour provided, scaled by the global
                 brightness of the board.
        """
        return (0.2126 * colour[0] +
                0.7152 * colour[1] +
                0.0722 * colour[2]) / (100 * self._max_brightness)

    def _write_colour(self, colour):
        """ Write a single colour to the whole board

        :param colour: RGB colour to write to the board.
        """
        self._leds.fill(colour)
