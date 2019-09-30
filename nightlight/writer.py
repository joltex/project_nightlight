import json
import logging
import os

from nightlight import base

DEFAULT_RESOLUTION = (30, 18)


def main(args):
    """
    Commandline entrypoint - Play function
    """
    patterns = load_nightlight_files(args.path)
    board = base.Nightlight(max_brightness=0.5, default_frame_rate=args.frame_rate)
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
            with open(file_path, 'r') as file_handler:
                result.append(json.load(file_handler))
        except:
            logging.error("Could not load nightlight file %r", file_path)
    return result


def start_the_show(board, patterns):
    while 1:
        for pattern in patterns:
            board._write_colour((0, 0, 0))
            board.write_pattern(pattern)
