import pytest

import numpy as np

from nightlight.sources.file import File


@pytest.fixture
def test_pattern():
    """Create a test pattern where all rgb values for frame 1 are (1, 1, 1), all
    rgb values for frame 2 are (2, 2, 2), etc."""
    num_frames = 3
    width = 30
    height = 18
    num_channels = 3

    pattern = np.zeros((num_frames, height, width, num_channels), dtype=np.uint8)
    for i in range(num_frames):
        pattern[i] = np.full((height, width, num_channels), i + 1, dtype=np.uint8)

    return pattern


def test_file(tmp_path, test_pattern):
    test_file = tmp_path / "test.nl"
    with open(test_file, "wb") as fout:
        np.save(fout, test_pattern)

    file_source = File(test_file)
    assert file_source.data.shape == test_pattern.shape
    for i in range(0, 3):
        assert np.array_equal(file_source.get_frame(), test_pattern[i])
    assert np.array_equal(file_source.get_frame(), test_pattern[0])
