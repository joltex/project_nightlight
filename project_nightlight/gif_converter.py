import json
from PIL import Image, GifImagePlugin


def write_rgb_map_to_file(rgb_map, outfile):
    with open(outfile, 'w') as fout:
        json.dump(rgb_map, fout, indent=2)


def get_rgb_map_from_gif(gif_file):
    # Create an Image object from the gif file.
    gif_obj = Image.open(gif_file)
    # gif_obj = gif_obj.convert('RGB')

    # Iterate through each frame of the gif and read the RGB values for each pixel.
    rgb_map = []
    for frame in range(0, gif_obj.n_frames):
        gif_obj.seek(frame)
        rgb_map.append(get_rgb_map_from_frame(gif_obj))

    return rgb_map


def get_rgb_map_from_frame(img_obj):
    """ Parse the RGB value for each pixel in a pillow image object

    :param img_obj:
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
