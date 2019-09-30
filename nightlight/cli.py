""" converter.py

This module contains functions for converting video files to Nightlight files - text files
which store the RGB values for each pixel in each frame of a video. These files can then be
read by the Nightlight.

"""
import argparse

import nightlight.subcommands.converter as _converter
import nightlight.subcommands.writer as _writer


def main():
    """
    Commandline entrypoint - parses args and calls process_video().
    """
    parser = argparse.ArgumentParser(prog="nightlight")
    subparsers = parser.add_subparsers(help="subparser for Nighlight")

    # Converter
    converter = subparsers.add_parser('convert', help="Tool to to convert images into nighlight files (.nl)")
    converter.add_argument('path', help='Path to a video file or a directory of video files.')
    converter.add_argument('-o', '--outdir', help='Directory to save the converted video(s) to.')
    converter.add_argument('-r', '--resolution', type=str, help='Resolution to scale the video to -'
                                                             ' width x height. eg 30x18')
    converter.add_argument('-f', '--fps', type=int, help='Frames per second to use when converting'
                                                       ' the video to frames')
    converter.add_argument('-s', '--scale_method', help='Scaling method to use (bicubic, neighbor,'
                                                     ' gauss, etc.)')
    converter.add_argument('-c', '--contrast', type=float, help='-1000.0 to 1000.0')
    converter.add_argument('-b', '--brightness', type=float, help='-1.0 to 1.0')
    converter.add_argument('-a', '--saturation', type=float, help='0.0 to 3.0')
    converter.add_argument('-g', '--gamma', type=float, help='0.1 to 10.0')
    converter.set_defaults(func=_converter.main)


    play = subparsers.add_parser('play', help="Tool to play nightlight files on a board.")
    play.add_argument('path', help='path to a nightlight file or directory of nightlight files.')
    play.add_argument('--frame_rate', type=int, help='frame rate in frames-per-second.', default=30)
    play.set_defaults(func=_writer.main)

    args = parser.parse_args()
    args.func(args)
