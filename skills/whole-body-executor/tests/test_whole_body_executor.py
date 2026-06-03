import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from whole_body_executor import allocate_task_delta, support_polygon_margin


def test_allocate_task_delta_sums_to_task():
    base, arm = allocate_task_delta([1, 2, 3], 0.25)
    assert np.allclose(base + arm, [1, 2, 3])


def test_support_margin_inside_positive():
    margin = support_polygon_margin([0, 0], [[-1, -1], [1, -1], [1, 1], [-1, 1]])
    assert margin > 0

