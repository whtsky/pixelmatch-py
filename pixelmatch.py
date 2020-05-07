import functools
from typing import Sequence, Union, List

try:
    from PIL import ImageDraw
except ImportError:
    ImageDraw = False

DEFAULT_OPTIONS = {
    "threshold": 0.1,  # matching threshold (0 to 1); smaller is more sensitive
    "includeAA": False,  # whether to skip anti-aliasing detection
    "alpha": 0.1,  # opacity of original image in diff ouput
    "aa_color": [255, 255, 0],  # color of anti-aliased pixels in diff output
    "diff_color": [255, 0, 0],  # color of different pixels in diff output
    "diff_mask": False,  # draw the diff over a transparent background (a mask)
}

ImageData = List[int]
ImageOrImageArray = Union["Image", Sequence[float]]


def pixelmatch(
    img1: ImageOrImageArray,
    img2: ImageOrImageArray,
    width: int = None,
    height: int = None,
    output: ImageOrImageArray = None,
    options=None,
    **kwargs,
):
    img1_size, img1 = extract_size_and_convert_to_image_array(img1)
    img2_size, img2 = extract_size_and_convert_to_image_array(img2)

    if img1_size:
        width1, height1 = img1_size
    else:
        width1, height1 = width, height

    if img2_size:
        width2, height2 = img2_size
    else:
        width2, height2 = width, height

    if len(img1) != len(img2) or (output and len(output) != len(img1)):
        raise ValueError("Image sizes do not match.", len(img1), len(img2), len(output))
    if width2 != width1 or height2 != height1:
        raise ValueError(
            f"Image sizes do not match: {width1}x{height1} vs {width2}x{height2}"
        )

    if len(img1) != width * height * 4:
        raise ValueError(
            "Image data size does not match width/height.",
            len(img1),
            width * height * 4,
        )

    options = options or {}
    options = {**DEFAULT_OPTIONS, **options, **kwargs}

    # fast path if identical
    if img1 == img2:
        if output and not options["diff_mask"]:
            if not is_PIL_image(output):
                for i in range(width * height):
                    draw_gray_pixel(img1, 4 * i, options["alpha"], output)
            else:
                for i in range(width * height):
                    pass

        return 0

    # maximum acceptable square distance between two colors;
    # 35215 is the maximum possible value for the YIQ difference metric
    maxDelta = 35215 * options["threshold"] * options["threshold"]

    diff = 0
    [aaR, aaG, aaB] = options["aa_color"]
    [diffR, diffG, diffB] = options["diff_color"]

    # compare each pixel of one image against the other one
    for y in range(height):
        for x in range(width):
            pos = (y * width + x) * 4

            # squared YUV distance between colors at this pixel position
            delta = color_delta(img1, img2, pos, pos)

            # the color difference is above the threshold
            if delta > maxDelta:
                # check it's a real rendering difference or just anti-aliasing
                if not options["includeAA"] and (
                    antialiased(img1, x, y, width, height, img2)
                    or antialiased(img2, x, y, width, height, img1)
                ):
                    # one of the pixels is anti-aliasing; draw as yellow and do not count as difference
                    # note that we do not include such pixels in a mask
                    if output and not options["diff_mask"]:
                        draw_pixel(output, pos, aaR, aaG, aaB)
                else:
                    # found substantial difference not caused by anti-aliasing; draw it as red
                    if output:
                        draw_pixel(output, pos, diffR, diffG, diffB)
                    diff += 1

            elif output:
                # pixels are similar; draw background as grayscale image blended with white
                if not options["diff_mask"]:
                    draw_gray_pixel(img1, pos, options["alpha"], output)

    # return the number of different pixels
    return diff


def antialiased(img, x1, y1, width, height, img2):
    """
    check if a pixel is likely a part of anti-aliasing;
    based on "Anti-aliased Pixel and Intensity Slope Detector" paper by V. Vysniauskas, 2009
    """
    x0 = max(x1 - 1, 0)
    y0 = max(y1 - 1, 0)
    x2 = min(x1 + 1, width - 1)
    y2 = min(y1 + 1, height - 1)
    pos = (y1 * width + x1) * 4
    zeroes = (x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2) and 1 or 0
    min_delta = max_delta = min_x = min_y = max_x = max_y = 0

    # go through 8 adjacent pixels
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue

            # brightness delta between the center pixel and adjacent one
            delta = color_delta(img, img, pos, (y * width + x) * 4, True)

            # count the number of equal, darker and brighter adjacent pixels
            if delta == 0:
                zeroes += 1
                # if found more than 2 equal siblings, it's definitely not anti-aliasing
                if zeroes > 2:
                    return False

            # remember the darkest pixel
            elif delta < min_delta:
                min_delta = delta
                min_x = x
                min_y = y

            # remember the brightest pixel
            elif delta > max_delta:
                max_delta = delta
                max_x = x
                max_y = y

    # if there are no both darker and brighter pixels among siblings, it's not anti-aliasing
    if min_delta == 0 or max_delta == 0:
        return False

    # if either the darkest or the brightest pixel has 3+ equal siblings in both images
    # (definitely not anti-aliased), this pixel is anti-aliased
    return (
        has_many_siblings(img, min_x, min_y, width, height)
        and has_many_siblings(img2, min_x, min_y, width, height)
    ) or (
        has_many_siblings(img, max_x, max_y, width, height)
        and has_many_siblings(img2, max_x, max_y, width, height)
    )


def has_many_siblings(img, x1, y1, width, height):
    """
    check if a pixel has 3+ adjacent pixels of the same color.
    """
    x0 = max(x1 - 1, 0)
    y0 = max(y1 - 1, 0)
    x2 = min(x1 + 1, width - 1)
    y2 = min(y1 + 1, height - 1)
    pos = (y1 * width + x1) * 4
    zeroes = (x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2) and 1 or 0

    # go through 8 adjacent pixels
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue

            pos2 = (y * width + x) * 4
            if all(img[pos + offset] == img[pos2 + offset] for offset in range(4)):
                zeroes += 1

            if zeroes > 2:
                return True

    return False


def color_delta(img1, img2, k: int, m, y_only=False):
    """
    calculate color difference according to the paper "Measuring perceived color difference
    using YIQ NTSC transmission color space in mobile applications" by Y. Kotsarenko and F. Ramos
    """
    r1, g1, b1, a1 = [img1[k + offset] for offset in range(3)]
    r2, g2, b2, a2 = [img2[k + offset] for offset in range(3)]

    if a1 == a2 and r1 == r2 and g1 == g2 and b1 == b2:
        return 0

    if a1 < 255:
        a1 /= 255
        r1, b1, g1 = blendRGB(r1, b1, g1, a1)

    if a2 < 255:
        a2 /= 255
        r2, b2, g2 = blendRGB(r2, b2, g2, a2)

    y = rgb2y(r1, g1, b1) - rgb2y(r2, g2, b2)

    if y_only:
        # brightness difference only
        return y

    i = rgb2i(r1, g1, b1) - rgb2i(r2, g2, b2)
    q = rgb2q(r1, g1, b1) - rgb2q(r2, g2, b2)

    return 0.5053 * y * y + 0.299 * i * i + 0.1957 * q * q


def rgb2y(r: int, g: int, b: int):
    return r * 0.29889531 + g * 0.58662247 + b * 0.11448223


def rgb2i(r: int, g: int, b: int):
    return r * 0.59597799 - g * 0.27417610 - b * 0.32180189


def rgb2q(r: int, g: int, b: int):
    return r * 0.21147017 - g * 0.52261711 + b * 0.31114694


def blendRGB(r: int, g: int, b: int, a):
    return blend(r, a), blend(g, a), blend(b, a)


def blend(c: int, a):
    """blend semi-transparent color with white"""
    return 255 + (c - 255) * a


def draw_pixel(output, pos: int, r: int, g: int, b: int):
    output[pos + 0] = int(r)
    output[pos + 1] = int(g)
    output[pos + 2] = int(b)
    output[pos + 3] = 255


def draw_gray_pixel(img, i: int, alpha, output):
    r = img[i + 0]
    g = img[i + 1]
    b = img[i + 2]
    val = blend(rgb2y(r, g, b), alpha * img[i + 3] / 255)
    draw_pixel(output, i, val, val, val)


def extract_size_and_convert_to_image_array(img: ImageOrImageArray):
    """
    Takes a img of type ImageOrImageArray and extracts the size information from it if possible.
    :param img: PIL.Image or sequence in the format [R1, G1, B1, A1, R2, ...]
    :return: tuple of size, list of image data in the format [R1, G1, B1, A1, R2, ...]
    """
    if is_PIL_image(img):
        return img.size, [x for p in img.convert("RGBA").getdata() for x in p]
    return None, img


@functools.lru_cache()
def is_PIL_image(img: ImageOrImageArray):
    return (
        all(hasattr(img, attr) for attr in ["convert", "getdata"])
        and type(img).__name__ == "Image"
    )
