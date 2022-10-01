import copy
from nightlight.converter import write_rgb_array_to_file

DEFAULT_RESOLUTION = (30, 18)

empty_frame = [[[0, 0, 0] for x in range(DEFAULT_RESOLUTION[0])] for y in range(DEFAULT_RESOLUTION[1])]
lit_pixel = (100, 100, 100)


def generate_test_pattern():
    frames = []
    for i in range(DEFAULT_RESOLUTION[1]):
        for j in range(DEFAULT_RESOLUTION[0]):
            new_frame = copy.deepcopy(empty_frame)
            new_frame[i][j] = lit_pixel
            frames.append(new_frame)
    return frames


def create_test_pattern_file(path):
    pattern = generate_test_pattern()
    write_rgb_array_to_file(pattern, path)
