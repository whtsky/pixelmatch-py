import itertools
from pathlib import Path
from typing import Dict

import pytest
from PIL import Image

from pixelmatch import pixelmatch

FIXTURES_PATH = Path(__file__).parent / "fixtures"
OPTIONS = {"threshold": 0.05}


def read_img(name: str):
    return Image.open(FIXTURES_PATH / f"{name}.png")


def pil_to_flatten_data(img):
    """
    Convert data from [(R1, G1, B1, A1), (R2, G2, B2, A2)] to [R1, G1, B1, A1, R2, G2, B2, A2]
    """
    return [x for p in img.convert("RGBA").getdata() for x in p]


testdata = [
    ["1a", "1b", "1diff", OPTIONS, 143],
    [
        "1a",
        "1b",
        "1diffmask",
        {"threshold": 0.05, "includeAA": False, "diff_mask": True},
        143,
    ],
    ["1a", "1a", "1emptydiffmask", {"threshold": 0, "diff_mask": True}, 0],
    [
        "2a",
        "2b",
        "2diff",
        {
            "threshold": 0.05,
            "alpha": 0.5,
            "aa_color": [0, 192, 0],
            "diff_color": [255, 0, 255],
        },
        12437,
    ],
    ["3a", "3b", "3diff", OPTIONS, 212],
    ["4a", "4b", "4diff", OPTIONS, 36049],
    ["5a", "5b", "5diff", OPTIONS, 0],
    ["6a", "6b", "6diff", OPTIONS, 51],
    ["6a", "6a", "6empty", {"threshold": 0}, 0],
    ["7a", "7b", "7diff", OPTIONS, 9856],
]


@pytest.mark.parametrize(
    "img_path_1,img_path_2,diff_path,options,expected_mismatch", testdata
)
def test_pixelmatch(
    img_path_1: str,
    img_path_2: str,
    diff_path: str,
    options: Dict,
    expected_mismatch: int,
):

    img1 = read_img(img_path_1)
    img2 = read_img(img_path_2)
    width, height = img1.size
    img1_data = pil_to_flatten_data(img1)
    img2_data = pil_to_flatten_data(img2)
    diff_data = [0.0] * len(img1_data)

    mismatch = pixelmatch(img1_data, img2_data, width, height, diff_data, **options)
    mismatch2 = pixelmatch(img1_data, img2_data, width, height, None, **options)

    expected_diff = read_img(diff_path)
    assert diff_data == pil_to_flatten_data(expected_diff), "diff image"
    assert mismatch == expected_mismatch, "number of mismatched pixels"
    assert mismatch == mismatch2, "number of mismatched pixels without diff"
