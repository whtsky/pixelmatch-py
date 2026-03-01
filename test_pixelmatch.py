from pathlib import Path
from typing import Dict

import pytest
from PIL import Image
from pixelmatch.contrib import PIL

from pixelmatch import pixelmatch

FIXTURES_PATH = Path(__file__).parent / "fixtures"
OPTIONS = {"threshold": 0.05}


def read_img(name: str):
    return Image.open(FIXTURES_PATH / f"{name}.png")


def pil_to_flatten_data(img):
    """
    Convert data from [(R1, G1, B1, A1), (R2, G2, B2, A2)] to [R1, G1, B1, A1, R2, G2, B2, A2]
    """
    return list(img.convert("RGBA").tobytes())


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
    benchmark,
):

    img1 = read_img(img_path_1)
    img2 = read_img(img_path_2)
    width, height = img1.size
    img1_data = pil_to_flatten_data(img1)
    img2_data = pil_to_flatten_data(img2)
    diff_data = [0.0] * len(img1_data)

    mismatch = benchmark(
        pixelmatch, img1_data, img2_data, width, height, diff_data, **options
    )
    mismatch2 = pixelmatch(img1_data, img2_data, width, height, None, **options)

    expected_diff = read_img(diff_path)
    assert diff_data == pil_to_flatten_data(expected_diff), "diff image"
    assert mismatch == expected_mismatch, "number of mismatched pixels"
    assert mismatch == mismatch2, "number of mismatched pixels without diff"


@pytest.mark.parametrize(
    "img_path_1,img_path_2,diff_path,options,expected_mismatch", testdata
)
def test_pixelmatch_failfast(
    img_path_1: str,
    img_path_2: str,
    diff_path: str,
    options: Dict,
    expected_mismatch: int,
    benchmark,
):
    img1 = read_img(img_path_1)
    img2 = read_img(img_path_2)
    width, height = img1.size
    img1_data = pil_to_flatten_data(img1)
    img2_data = pil_to_flatten_data(img2)
    if expected_mismatch:
        assert (
            benchmark(
                pixelmatch,
                img1_data,
                img2_data,
                width,
                height,
                fail_fast=True,
                **options,
            )
            == 1
        )


@pytest.mark.parametrize(
    "img_path_1,img_path_2,diff_path,options,expected_mismatch", testdata
)
def test_PIL_pixelmatch(
    img_path_1: str,
    img_path_2: str,
    diff_path: str,
    options: Dict,
    expected_mismatch: int,
    benchmark,
):
    img1 = read_img(img_path_1)
    img2 = read_img(img_path_2)
    diff_data = Image.new("RGBA", img1.size)

    mismatch = benchmark(PIL.pixelmatch, img1, img2, diff_data, **options)
    mismatch2 = PIL.pixelmatch(img1, img2, **options)

    assert pil_to_flatten_data(diff_data) == pil_to_flatten_data(
        read_img(diff_path)
    ), "diff image"
    assert mismatch == expected_mismatch, "number of mismatched pixels"
    assert mismatch == mismatch2, "number of mismatched pixels without diff"

def test_PIL_pixelmatch_identical_images_diff_mask_output_stays_blank(benchmark):
    """
    When diff_mask=True and images are identical, output must remain blank
    and the return value must be 0.
    """
    img = read_img("1a")
    output = Image.new("RGBA", img.size)

    result = benchmark(PIL.pixelmatch, img, img, output, threshold=0, diff_mask=True)

    assert result == 0
    assert list(output.tobytes()) == [0] * len(output.tobytes())


@pytest.mark.parametrize(
    "alpha,fixture",
    [
        (0.0, "1a_identical_alpha00"),
        (0.1, "1a_identical_alpha01"),
        (0.5, "1a_identical_alpha05"),
        (1.0, "1a_identical_alpha10"),
    ],
)
def test_PIL_pixelmatch_identical_images_output_matches_core(alpha, fixture, benchmark):
    """
    For identical images with output requested, PIL.pixelmatch must produce
    the same pixel values as core.pixelmatch for any alpha value.
    Golden fixtures were generated from core.pixelmatch on master.
    """
    img = read_img("1a")
    pil_output = Image.new("RGBA", img.size)
    benchmark(PIL.pixelmatch, img, img, pil_output, threshold=0, alpha=alpha)
    assert pil_to_flatten_data(pil_output) == pil_to_flatten_data(read_img(fixture))


@pytest.mark.parametrize(
    "alpha,fixture",
    [
        (0.0, "transparent_identical_alpha00"),
        (0.1, "transparent_identical_alpha01"),
        (0.5, "transparent_identical_alpha05"),
        (1.0, "transparent_identical_alpha10"),
    ],
)
def test_PIL_pixelmatch_identical_transparent_images_output_matches_core(
    alpha, fixture, benchmark
):
    """
    For identical fully-transparent images with output requested,
    PIL.pixelmatch must produce the same pixel values as core.pixelmatch
    for any alpha value.
    Golden fixtures were generated from core.pixelmatch on master.
    """
    img = Image.new("RGBA", (4, 4), (100, 150, 200, 0))
    pil_output = Image.new("RGBA", img.size)
    benchmark(PIL.pixelmatch, img, img, pil_output, threshold=0, alpha=alpha)
    assert pil_to_flatten_data(pil_output) == pil_to_flatten_data(read_img(fixture))