""" perlin.py

This module contains functions for generating pattern arrays using Perlin noise.

Once a base noise pattern has been generated using simplex_noise4d(), masks such
as quantize() and colourize() can be applied on top of it.

See https://github.com/LoicGoulefert/perlin-gif for more info.

"""
import math
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from noise import snoise4


def _simplex_noise4d(shape: Tuple[int, int, int], scale: Tuple[int, int, int],
                     octaves: int = 1, radius: float = 0.5, random: bool = False) -> np.ndarray:
    """ Return a sequence of images representing 4D (looping) simplex noise as an array

    :param shape:
    :param scale:
    :param octaves:
    :param radius:
    :param random:
    :return:
    """
    frames = np.zeros(shape)
    offset = np.random.rand() * 100 if random else 0

    for i in range(shape[2]):
        cos_value = radius * math.cos(2 * math.pi * (i / shape[2]))
        sin_value = radius * math.sin(2 * math.pi * (i / shape[2]))
        for x in range(shape[0]):
            for y in range(shape[1]):
                frames[x, y, i] = snoise4(x * scale[0] + offset, y * scale[1] + offset,
                                          cos_value, sin_value, octaves=octaves)
    frames = ((frames - frames.min()) * (1 / (frames.max() - frames.min()) * 255)).astype('uint8')

    return frames.transpose(2, 0, 1)


def _quantize(frames: np.ndarray, bins: int = 2) -> np.ndarray:
    """ Apply quantization to a noise pattern

    :param frames: Input noise pattern array.
    :param bins: Number of bins to quantize to.
    :return: Input pattern quantized to `bins`.
    """
    w = frames.max() / bins
    for i in range(frames.shape[0]):
        frames[i, :, :] -= (frames[i, :, :] - (frames[i, :, :] // w) * w).astype('uint8')
    return frames


def _colourize(frames: np.ndarray, colourmap: str = 'gist_rainbow') -> np.ndarray:
    """ Colour a greyscale noise pattern using a colour map

    :param frames: Input noise pattern array.
    :param colourmap: Matplotlib colour map to use.
    :return: Colourized input frames.
    """
    cm = plt.get_cmap(colourmap)
    frames = frames.astype('float64')
    # Normalize all values to be between 0 and 1
    frames *= 1/frames.max()
    # Apply the colour map to each frame and reset values to 0-255
    coloured_frames = np.stack([np.uint8(cm(frame) * 255) for frame in frames])
    return coloured_frames
