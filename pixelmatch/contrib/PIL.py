"""Functions to facilitate direct comparison of PIL.Image instances"""
from typing import List, Optional, Tuple

from PIL.Image import Image

from pixelmatch import core
from pixelmatch.types import ImageSequence, MutableImageSequence, RGBTuple


def pixelmatch(
    img1: Image,
    img2: Image,
    output: Optional[Image] = None,
    threshold: float = 0.1,
    includeAA: bool = False,
    alpha: float = 0.1,
    aa_color: RGBTuple = (255, 255, 0),
    diff_color: RGBTuple = (255, 0, 0),
    diff_mask: bool = False,
    fail_fast: bool = False,
) -> int:
    """
    Compares two images, writes the output diff and returns the number of mismatched pixels.
    Serves the same purpose as pixelmatch.pixelmatch, but takes PIL.Images as input instead
    of raw image data.

    :param img1: PIL.Image data to compare with img2. Must be the same size as img2
    :param img2: PIL.Image data to compare with img2. Must be the same size as img1
    :param output: Image data to write the diff to. Should be the same size as
    :param threshold: matching threshold (0 to 1); smaller is more sensitive, defaults to 1
    :param includeAA: whether or not to skip anti-aliasing detection, ie if includeAA is True,
        detecting and ignoring anti-aliased pixels is disabled. Defaults to False
    :param alpha: opacity of original image in diff output, defaults to 0.1
    :param aa_color: tuple of RGB color of anti-aliased pixels in diff output,
        defaults to (255, 255, 0) (yellow)
    :param diff_color: tuple of RGB color of the color of different pixels in diff output,
        defaults to (255, 0, 0) (red)
    :param diff_mask: whether or not to draw the diff over a transparent background (a mask),
        defaults to False
    :param fail_fast: if true, will return after first different pixel. Defaults to false
    :return: number of pixels that are different or 1 if fail_fast == true
    """
    width, height = img1.size
    img1 = from_PIL_to_raw_data(img1)
    img2 = from_PIL_to_raw_data(img2)

    if output is not None:
        raw_output: Optional[MutableImageSequence] = from_PIL_to_raw_data(output)
    else:
        raw_output = None

    diff_pixels = core.pixelmatch(
        img1,
        img2,
        width,
        height,
        raw_output,
        threshold=threshold,
        includeAA=includeAA,
        alpha=alpha,
        aa_color=aa_color,
        diff_color=diff_color,
        diff_mask=diff_mask,
        fail_fast=fail_fast,
    )

    if raw_output is not None and output is not None:
        output.putdata(to_PIL_from_raw_data(raw_output))

    return diff_pixels


def from_PIL_to_raw_data(pil_img: Image) -> MutableImageSequence:
    """
    Converts a PIL.Image object from [(R1, B1, A1, A1), (R2, ...), ...] to our raw data format
    [R1, G1, B1, A1, R2, ...].

    :param pil_img:
    :return:
    """
    return [item for sublist in pil_img.convert("RGBA").getdata() for item in sublist]


def to_PIL_from_raw_data(
    raw_data: ImageSequence,
) -> List[Tuple[float, float, float, float]]:
    """
    Converts from the internal raw data format of [R1, G1, B1, A1, R2, ...] to PIL's raw data format, ie
    [(R1, B1, A1, A1), (R2, ...), ...]
    :return: raw image data in a PIL appropriate format
    """
    return [*zip(raw_data[::4], raw_data[1::4], raw_data[2::4], raw_data[3::4])]
