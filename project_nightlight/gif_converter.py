import json
from PIL import Image, GifImagePlugin


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
    :param outfile: Path to file to write the RGB map to.
    :param pretty: If True, write the RGB map to the file using newlines to separate each row of
                   each frame.
    """
    if pretty:
        write_rgb_map_to_file_pretty(rgb_map, outfile)
    else:
        with open(outfile, 'w') as fout:
            json.dump(rgb_map, fout)


def write_rgb_map_to_file_pretty(rgb_map, outfile):
    with open(outfile, 'w') as fout:
        for i, frame in enumerate(rgb_map):
            fout.write(f'# Frame {i+1}\n')
            for row in frame:
                json.dump(row, fout)
                fout.write('\n')
