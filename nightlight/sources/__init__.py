# TODO: Uncomment once we move to at least Python 3.8 which has Protocol support
# from typing import Protocol
#
# import numpy as np
#
#
# class Source(Protocol):
#     """Sources supply image data to display on the board.
#
#     A source must implement at least a `get_frame()` method for the Nightlight player to call.
#     """
#     def get_frame(self) -> np.ndarray:
#         ...
