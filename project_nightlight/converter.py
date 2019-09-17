""" converter.py

This module contains functions for converting video files to Nightlight files - text files
which store the RGB values for each pixel in each frame of a video. These files can then be
read by the Nightlight.

"""
import json
import os
from PIL import Image, GifImagePlugin


def convert_frames_to_file(frames, outfile):
    """ Convert a collection of video frames to a Nightlight file

    :param frames: Either a path to a directory of images or a list of Pillow Image objects. If
                   frames is a path, the frame order is expected to match the alphanumeric
                   order of the filenames (eg 1.png, 2.png etc.). If frames is a list, the frame
                   order is expected to match the order of the list elements.
    :param outfile: Output file path.
    """
    def validate_input(frames):
        valid_extensions = ['.png', '.jpg']
        if isinstance(frames, str) and os.path.isdir(frames):
            files = [x for x in os.listdir(frames) if x.endswith(tuple(valid_extensions))]
            files.sort()
            image_objs = [Image.open(os.path.join(frames, x)) for x in files]
        elif isinstance(frames, list):
            if not all(isinstance(x, Image.Image) for x in frames):
                raise TypeError('frames must be a directory or a list of Pillow Image objects.')
            image_objs = frames
        else:
            raise TypeError('frames must be a directory or a list of Pillow Image objects.')
        return image_objs

    image_objs = validate_input(frames)
    rgb_map = [get_rgb_map_from_image(x) for x in image_objs]
    write_rgb_map_to_file(rgb_map, outfile)


def get_rgb_map_from_gif(gif_file):
    # Create an Image object from the gif file.
    gif_obj = Image.open(gif_file)
    # gif_obj = gif_obj.convert('RGB')

    # Iterate through each frame of the gif and read the RGB values for each pixel.
    rgb_map = []
    for frame in range(0, gif_obj.n_frames):
        gif_obj.seek(frame)
        rgb_map.append(get_rgb_map_from_image(gif_obj))

    return rgb_map


def get_rgb_map_from_image(img_obj):
    """ Parse the RGB value for each pixel in a Pillow Image object

    :param img_obj: Pillow Image object.
    :return: List where each element is a list of RGB values representing one row
             of the image.
    """
    rgb_map = []
    width, height = img_obj.size
    for y in range(height):
        row_rgb_map = []
        for x in range(width):
            row_rgb_map.append(img_obj.getpixel((x, y)))
        rgb_map.append(row_rgb_map)

    return rgb_map


def write_rgb_map_to_file(rgb_map, outfile, pretty=False):
    """ Write an RGB map to a text file

    :param rgb_map: RGB map data structure - nested list where 1st level = frames of a video,
                    2nd level = rows of a frame, 3rd level = RGB values of a row.
    :param outfile: Output file path.
    :param pretty: If True, write the RGB map to the file using newlines to separate each row of
                   each frame.
    """
    if pretty:
        write_rgb_map_to_file_pretty(rgb_map, outfile)
    else:
        with open(outfile, 'w') as fout:
            json.dump(rgb_map, fout)


def write_rgb_map_to_file_pretty(rgb_map, outfile):
    """ Write an RGB map to a text file in a human-readable format

    Output format:
        # Frame 1
        [(102, 255, 130), (200, 173, 87)]
        [(200, 39, 150), (10, 144, 87)]
        # Frame 2
        [(56, 23, 0), (255, 66, 120)]
        ...

    :param rgb_map: RGB map data structure - nested list where 1st level = frames of a video,
                    2nd level = rows of a frame, 3rd level = RGB values of a row.
    :param outfile: Output file path.
    """
    with open(outfile, 'w') as fout:
        for i, frame in enumerate(rgb_map):
            fout.write(f'# Frame {i+1}\n')
            for row in frame:
                json.dump(row, fout)
                fout.write('\n')
