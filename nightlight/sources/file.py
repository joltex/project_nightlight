from __future__ import annotations

import json
import pathlib

import attr as attrs  # TODO >= Python 3.8: Replace with `import attrs`
import numpy as np

# from nightlight.sources import Source  # TODO >= Python 3.8: uncomment


@attrs.define
class File:  # TODO >= Python 3.8: Implement Source protocol
    """A File source reads image data from a .nl file (patent pending)."""
    path: str | pathlib.Path = attrs.field(converter=pathlib.Path)
    data: np.ndarray = attrs.field(init=False)
    current_frame: int = 0

    def __attrs_post_init__(self):
        try:
            # New format, numpy binary files
            with open(self.path, 'rb') as fin:
                self.data = np.load(fin)
        except ValueError:
            # Old format, nested list files TODO: Remove this after all files are converted
            with open(self.path, 'r') as fin:
                self.data = np.asarray(json.load(fin))

    def get_frame(self) -> np.ndarray:
        """Return the current frame from self.data.

        Loop back to the first frame once the last frame is reached.
        """
        frame = self.data[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.data)
        return frame
