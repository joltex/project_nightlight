""" converter.py

This module contains functions for converting video files to Nightlight files - text files
which store the RGB values for each pixel in each frame of a video. These files can then be
read by the Nightlight.

"""
import json
import os
import subprocess
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

DEFAULT_RESOLUTION = (30, 18)


def convert_frames_to_file(frames, outfile):
    """ Convert a collection of video frames to a Nightlight file

    :param frames: Either a path to a directory of images or a list of Pillow Image objects. If
                   frames is a path, the frame order is expected to match the alphanumeric
                   order of the filenames (eg 1.png, 2.png etc.). If frames is a list, the frame
                   order is expected to match the order of the list elements.
    :param outfile: Output file path.
    """
    valid_extensions = ['.png', '.jpg']
    if isinstance(frames, str) and os.path.isdir(frames):
        files = [x for x in os.listdir(frames) if x.endswith(tuple(valid_extensions))]
        files.sort()
        rgb_map = [get_rgb_map_from_image(Image.open(os.path.join(frames, x))) for x in files]

    elif isinstance(frames, list):
        if not all(isinstance(x, Image.Image) for x in frames):
            raise TypeError('frames must be a directory or a list of Pillow Image objects.')
        rgb_map = [get_rgb_map_from_image(x) for x in frames]

    else:
        raise TypeError('frames must be a directory or a list of Pillow Image objects.')

    write_rgb_array_to_file(rgb_map, outfile)


def convert_video_to_frames(video_file, outdir, fps=30):
    """ Convert a video file to a collection of frames (saved as image files) using ffmpeg

    This function requires that ffmpeg by available on the system path.

    :param video_file: Input video file path.
    :param outdir: Directory path to save the frame images to.
    :param fps: Frames per second to use.
    """
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    outpath = os.path.join(outdir, '%d.png')

    cmd = f'ffmpeg -i {video_file} -vf fps={fps} {outpath}'
    print(cmd)
    output = subprocess.check_output(cmd.split())
    print(output)


def get_ffmpeg_supported_formats():
    """ Get a list of video formats supported by the local ffmpeg installation

    :return: List of file extensions supported by the local ffmpeg installation.
    """
    supported_formats = []
    r = subprocess.check_output(['ffmpeg', '-formats'], universal_newlines=True)
    for line in r.split('\n')[4:]:
        if line.startswith(' D') or line.startswith('  E'):
            supported_formats.append(line.split()[1])
    return supported_formats


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


def process_video(path, outdir=None, resolution=DEFAULT_RESOLUTION, fps=30, **kwargs):
    """ Fully process a video or directory of videos into Nightlight format

    Scale the video to the appropriate resolution, convert it to frames, and then parse the RGB
    values from each frame.

    :param str path: Either a path to an input video file or a directory of video files.
    :param str outdir: Output directory path. If None, output will be saved to the input
                       directory.
    :param tuple resolution: Resolution in pixels to scale the video to (width, height).
    :param int fps: Frames per second to use.
    :param kwargs: Any valid arguments to scale_video().
    """
    def create_outdir(video, outdir):
        basedir = os.path.dirname(video)
        basename = os.path.basename(video)
        if outdir is None:
            video_outdir = os.path.join(basedir, os.path.splitext(basename)[0])
        else:
            video_outdir = os.path.join(outdir, os.path.splitext(basename)[0])
        if not os.path.exists(video_outdir):
            os.makedirs(video_outdir)
        return video_outdir

    def validate_input(path):
        valid_extensions = get_ffmpeg_supported_formats()
        if isinstance(path, str) and os.path.isdir(path):
            videos = [os.path.join(path, x) for x in os.listdir(path) if x.endswith(tuple(valid_extensions))]
        elif isinstance(path, str) and os.path.exists(path):
            videos = [path] if path.endswith(tuple(valid_extensions)) else []
        else:
            raise TypeError('Input must be either a video file or a directory of video files')
        if not videos:
            raise ValueError('Input does not include any video files with recognized extensions'
                             ' ({})'.format(valid_extensions))
        return videos

    videos = validate_input(path)
    for video in videos:
        video_outdir = create_outdir(video, outdir)
        video_filename = os.path.basename(video)

        # Scale the video.
        scaled_filename = '{}_({}x{}){}'.format(os.path.splitext(video_filename)[0], resolution[0],
                                                 resolution[1], os.path.splitext(video_filename)[1])
        scaled_video = os.path.join(video_outdir, scaled_filename)
        scale_video(video, scaled_video, resolution, **kwargs)

        # Convert the video to frames.
        frames_outdir = os.path.join(video_outdir, 'frames')
        convert_video_to_frames(scaled_video, frames_outdir, fps)

        # Convert the frames to a Nightlight file.
        nightlight_filename = '{}.nl'.format(os.path.splitext(video_filename)[0])
        convert_frames_to_file(frames_outdir, os.path.join(video_outdir, nightlight_filename))


def scale_video(infile, outfile, resolution=DEFAULT_RESOLUTION, scale_method='bicubic',
                contrast=1.0, brightness=0.0, saturation=1.0, gamma=1.0):
    """ Scale a video using ffmpeg

    You can choose a specific scaling method and apply equalizer adjustments such as contrast,
    brightness, and saturation to tune the appearance of the output video.

    This function requires that ffmpeg by available on the system path, and, if built from
    source, configured using the --enable-gpl flag.

    See ffmpeg scaler options here: https://ffmpeg.org/ffmpeg-scaler.html#scaler_005foptions
    See ffmpeg filter options here: https://ffmpeg.org/ffmpeg-filters.html#eq

    :param str infile: Input video file path.
    :param str outfile: Output video file path.
    :param tuple resolution: Resolution in pixels to scale the video to (width, height).
    :param str scale_method: Scaling method to use. Some examples are 'bicubic' and 'neighbor'.
    :param float contrast: Contrast adjustment factor (-1000.0 to 1000.0).
    :param float brightness: Brightness adjustment factor (-1.0 to 1.0).
    :param float saturation: Saturation adjustment factor (0.0 to 3.0).
    :param float gamma: Gamma adjustment factor (0.1 to 10.0).
    """
    cmd = (f'ffmpeg -i {infile} -vf scale={resolution[0]}:{resolution[1]}:flags={scale_method},'
           f'eq=contrast={contrast}:brightness={brightness}:saturation={saturation}:gamma={gamma}'
           f' -y {outfile}')
    print(cmd)
    output = subprocess.check_output(cmd.split())
    print(output)


def write_rgb_array_to_file(rgb_array, outfile, pretty=False):
    """ Write an array of RGB values to a text file

    :param rgb_array: RGB array - nested list where 1st level = frames of a video,
                    2nd level = rows of a frame, 3rd level = RGB values of a row.
    :param outfile: Output file path.
    :param pretty: If True, write the RGB map to the file using newlines to separate each row of
                   each frame.
    """
    if pretty:
        write_rgb_array_to_file_pretty(rgb_array, outfile)
    else:
        with open(outfile, 'w') as fout:
            json.dump(rgb_array, fout)


def write_rgb_array_to_file_pretty(rgb_array, outfile):
    """ Write an array of RGB values to a text file in a human-readable format

    Output format:
        # Frame 1
        [(102, 255, 130), (200, 173, 87)]
        [(200, 39, 150), (10, 144, 87)]
        # Frame 2
        [(56, 23, 0), (255, 66, 120)]
        ...

    :param rgb_array: RGB array data structure - nested list where 1st level = frames
                      of a video, 2nd level = rows of a frame, 3rd level = RGB values
                      of a row.
    :param outfile: Output file path.
    """
    with open(outfile, 'w') as fout:
        for i, frame in enumerate(rgb_array):
            fout.write(f'# Frame {i+1}\n')
            for row in frame:
                json.dump(row, fout)
                fout.write('\n')


def write_rgb_array_to_gif(rgb_array: np.ndarray, outfile: str,
                           colour_mode: str = 'RGB', scale: int = 5,
                           fps: int = 30, padding: Optional[int] = None):
    """ Write an array of RGB values to a gif file

    :param rgb_array: RGB array data structure - nested list where 1st level = frames
                      of a video, 2nd level = rows of a frame, 3rd level = RGB values
                      of a row.
    :param outfile: Output file path.
    :param colour_mode: 'L' if values in `rgb_array` are single uint8 / black and white
                        values from 0-255. 'RGB' if values in `rgb_array` are uint8 RGB
                        tuples (0-255, 0-255, 0-255).
    :param scale: Scaling factor to apply.
    :param fps: Frames per second to use in exported gif.
    :param padding: If supplied, insert this many pixels of black space between each
                    pixel to simulate the appearance of patterns on the board.
    """

    def add_padding(frames: np.ndarray, n: int = 1) -> np.ndarray:
        """ Mock the appearance of patterns on the board by inserting black pixels
            (zeros) between each row and each column of each frame

        :param frames: Array of pattern frames.
        :param n: Number of rows/columns of zeros to insert between each existing
                  row and column.
        :return: Input frames with zeroes added.
        """
        # Initialize array of zeros
        zeros_shape = [frames.shape[0],
                       ((n + 1) * frames.shape[1] - n),
                       ((n + 1) * frames.shape[2] - n)]
        if len(frames.shape) == 4:  # if this is an RGB array we need an extra dimension
            zeros_shape.append(frames.shape[3])
        new_frames = np.zeros(tuple(zeros_shape), dtype=frames.dtype)
        # Splice in the original data
        for i, f in enumerate(frames):
            new_frames[i][::n + 1, ::n + 1] = f
        return new_frames

    if padding:
        rgb_array = add_padding(rgb_array, padding)
    # Convert each frame of the pattern to a PIL image and scale.
    images = [Image.fromarray(np.uint8(frame), mode=colour_mode)
              .resize((frame.shape[1] * scale, frame.shape[0] * scale))
              for frame in rgb_array]
    # For RGB patterns, need to map the images to a palette otherwise the gif looks whack.
    if colour_mode == 'RGB':
        images = [image.convert('P', palette=Image.ADAPTIVE)
                  for image in images]

    images[0].save(outfile, save_all=True, append_images=images[1:], duration=1/fps*100)
