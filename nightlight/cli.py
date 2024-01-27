""" cli.py

"""
import argparse

from nightlight import base, converter, player


def main():
    """ Configure the argument parsers, parse the arguments, and launch the appropriate command

    """
    parser = argparse.ArgumentParser(prog='nightlight')
    subparsers = parser.add_subparsers(title='commands', dest='command')
    configure_clear_parser(subparsers)
    configure_convert_parser(subparsers)
    configure_play_parser(subparsers)

    args = parser.parse_args()
    if args.command == 'clear':
        base.Nightlight().write_colour((0, 0, 0))
    if args.command == 'convert':
        converter.process_video(args.path, args.outdir, resolution=(args.width, args.height),
                                fps=args.fps, scale_method=args.scale_method,
                                contrast=args.contrast, brightness=args.brightness,
                                saturation=args.saturation, gamma=args.gamma)
    elif args.command == 'play':
        player.play_nightlight_files(args.path, args.max_brightness, args.frame_rate)


def configure_clear_parser(subparsers):
    """ Add the 'convert' arguments to an ArgumentParser object's subparsers

    :param subparsers: The argparse subparsers object to add the arguments to.
    """
    clear_parser = subparsers.add_parser('clear', help='Turn off all the lights.')


def configure_convert_parser(subparsers):
    """ Add the 'convert' arguments to an ArgumentParser object's subparsers

    :param subparsers: The argparse subparsers object to add the arguments to.
    """
    convert_parser = subparsers.add_parser('convert',
                                           help='Convert videos into Nightlight files (.nl).')
    convert_parser.add_argument('path', help='Path to a video file or directory of video files, or'
                                ' a YouTube http address.')
    convert_parser.add_argument('-o', '--outdir', default=None, help='Directory to save the converted video(s) to.')
    convert_parser.add_argument('-x', '--width', type=int, default=30,
                                help='Width in pixels to scale video to.')
    convert_parser.add_argument('-y', '--height', type=int, default=18,
                                help='Height in pixels to scale video to.')
    convert_parser.add_argument('-f', '--fps', type=int, default=30,
                                help='Frames per second to use when converting the video to frames')
    convert_parser.add_argument('-s', '--scale_method', default='bicubic',
                                help='Scaling method to use (bicubic, neighbor, gauss, etc.)')
    convert_parser.add_argument('-c', '--contrast', type=float, default=1.0, help='-1000.0 to 1000.0')
    convert_parser.add_argument('-b', '--brightness', type=float, default=0.0, help='-1.0 to 1.0')
    convert_parser.add_argument('-a', '--saturation', type=float, default=1.0, help='0.0 to 3.0')
    convert_parser.add_argument('-g', '--gamma', type=float, default=1.0, help='0.1 to 10.0')


def configure_play_parser(subparsers):
    """ Add the 'play' arguments to an ArgumentParser object's subparsers

    :param subparsers: The argparse subparsers object to add the arguments to.
    """
    play_parser = subparsers.add_parser('play', help='Play Nightlight files on a board.')
    play_parser.add_argument('path', help='Path to a Nightlight file or directory of Nightlight files.')
    play_parser.add_argument('-b', '--max_brightness', type=float, default=0.5,
                             help='The maximum global brightness to use (0.0 to 1.0).')
    play_parser.add_argument('-f', '--frame_rate', type=int, default=30,
                             help='Frame rate in frames-per-second.')
