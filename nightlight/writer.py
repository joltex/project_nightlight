import json
import logging
import os

from nightlight import base

DEFAULT_RESOLUTION = (30, 18)


    """
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
            with open(file_path, 'r') as file_handler:
                result.append(json.load(file_handler))
        except:
            logging.error("Could not load nightlight file %r", file_path)
    return result


def play_nightlight_files(path, max_brightness=1.0, frame_rate=30):
    """ Play a Nightlight file or directory of Nightlight files

    :param path: Path to a Nightlight file or directory of Nightlight files.
    :param max_brightness: The maximum global brightness during playback.
    :param frame_rate: The frame rate to use in frames per second.
    """
    patterns = load_nightlight_files(path)
    board = base.Nightlight(max_brightness=max_brightness, default_frame_rate=frame_rate)
    start_the_show(board, patterns)


def start_the_show(board, patterns):
    while 1:
        for pattern in patterns:
            board._write_colour((0, 0, 0))
            board.write_pattern(pattern)
