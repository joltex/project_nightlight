import json
import logging
import os

from nightlight import base


def get_file_paths(path, valid_extensions=None):
    """ Get all files at the given path that have an extension in valid_extensions

    :param path: Path to a single file or directory of files with particular extension(s).
    :param valid_extensions: List of valid extensions; return paths to all files at path which end
                             in any of these.
    :return: List of paths for all files at path that end in a valid extension.
    """
    if valid_extensions is None:  # If no valid extensions were supplied, consider all files valid.
        valid_extensions = ['']

    if isinstance(path, str) and os.path.isdir(path):
        files = [os.path.join(path, x) for x in os.listdir(path)
                 if x.endswith(tuple(valid_extensions))]
    elif isinstance(path, str) and os.path.exists(path):
        files = [path] if path.endswith(tuple(valid_extensions)) else []
    else:
        raise TypeError('Input must be either a Nightlight file or a directory of Nightlight files')
    if not files:
        raise ValueError('Input does not include any Nightlight files with recognized extensions'
                         ' ({})'.format(valid_extensions))

    return files


def load_nightlight_files(path):
    """ Read one or more Nightlight files into a list

    :param path: Path to a Nightlight file or directory of Nightlight files.
    :return: List of Nightlight pattern objects (nested list).
    """
    paths = get_file_paths(path, valid_extensions=['.nl'])
    result = []
    for file_path in paths:
        try:
            with open(file_path, 'r') as file_handler:
                result.append(json.load(file_handler))
        except:
            logging.error('Error loading Nightlight file {}'.format(file_path))
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
    """ Play one or more Nightlight patterns in a loop on the board

    :param board: Nightlight object to play on.
    :param patterns: List of patterns to play.
    """
    while 1:
        for pattern in patterns:
            board.write_colour((0, 0, 0))
            board.play_pattern(pattern)
