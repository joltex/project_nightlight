""" cli.py

"""
import argparse

from nightlight import converter, writer


def main():
    """ Configure the argument parses, parse the arguments, and launch the appropriate command

    """
    parser = argparse.ArgumentParser(prog='nightlight')
    subparsers = parser.add_subparsers(help='subparser for Nighlight')

    # Converter
    convert_parser = subparsers.add_parser('convert',
                                           help='Convert images into Nightlight files (.nl)')
    convert_parser.add_argument('path', help='Path to a video file or a directory of video files.')
    convert_parser.add_argument('-o', '--outdir', help='Directory to save the converted video(s) to.')
    convert_parser.add_argument('-r', '--resolution', type=str,
                                help='Resolution to scale the video to - width x height. eg 30x18')
    convert_parser.add_argument('-f', '--fps', type=int,
                                help='Frames per second to use when converting the video to frames')
    convert_parser.add_argument('-s', '--scale_method',
                                help='Scaling method to use (bicubic, neighbor, gauss, etc.)')
    convert_parser.add_argument('-c', '--contrast', type=float, help='-1000.0 to 1000.0')
    convert_parser.add_argument('-b', '--brightness', type=float, help='-1.0 to 1.0')
    convert_parser.add_argument('-a', '--saturation', type=float, help='0.0 to 3.0')
    convert_parser.add_argument('-g', '--gamma', type=float, help='0.1 to 10.0')
    convert_parser.set_defaults(func=converter.main)

    # Player
    play_parser = subparsers.add_parser('play', help='Tool to play nightlight files on a board.')
    play_parser.add_argument('path', help='Path to a Nightlight file or directory of Nightlight files.')
    play_parser.add_argument('--frame_rate', type=int, defaut=30,
                             help='Frame rate in frames-per-second.')
    play_parser.set_defaults(func=writer.main)

    args = parser.parse_args()
    args.func(args)
