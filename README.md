# pixelmatch-py

Python port of https://github.com/mapbox/pixelmatch with some additional support for PIL.Image objects.

A fast pixel-level image comparison library, originally created to compare screenshots in tests.

Features accurate **anti-aliased pixels detection**
and **perceptual color difference metrics**.

```python
from pixelmatch import pixelmatch

num_diff_pixels = pixelmatch(img1, img2, 800, 600, diff, threshold=0.1)
```

Implements ideas from the following papers:

- [Measuring perceived color difference using YIQ NTSC transmission color space in mobile applications](http://www.progmat.uaem.mx:8080/artVol2Num2/Articulo3Vol2Num2.pdf) (2010, Yuriy Kotsarenko, Fernando Ramos)
- [Anti-aliased pixel and intensity slope detector](https://www.researchgate.net/publication/234126755_Anti-aliased_Pixel_and_Intensity_Slope_Detector) (2009, Vytautas Vyšniauskas)

## Install

```bash
python -m pip install pixelmatch
```

## API

### pixelmatch(img1, img2, width, height[output, options])

- `img1`, `img2` — Image data to compare. Can be PIL.Image or raw image data in the format `[R1, G1, B1, A1, R2, G2, ...]`.
        **Note:** image dimensions must be equal.
- `width`, `height` — Width and height of the images. If left unspecified and either of `img1` and `img2` are instances of `PIL.Image`, the dimensions will be extracted from there. 
- `output` — Image data to write the diff to, or `None` if don't need a diff image. Can be a list containing raw image data or instance of `PIL.Image`. Note that _all three images_ need to have the same dimensions.
- `threshold` — Matching threshold, ranges from `0` to `1`. Smaller values make the comparison more sensitive. `0.1` by default.
- `includeAA` — If `true`, disables detecting and ignoring anti-aliased pixels. `false` by default.
- `alpha` — Blending factor of unchanged pixels in the diff output. Ranges from `0` for pure white to `1` for original brightness. `0.1` by default.
- `aa_color` — The color of anti-aliased pixels in the diff output in `[R, G, B]` format. `[255, 255, 0]` by default.
- `diff_color` — The color of differing pixels in the diff output in `[R, G, B]` format. `[255, 0, 0]` by default.
- `diff_mask` — Draw the diff over a transparent background (a mask), rather than over the original image. Will not draw anti-aliased pixels (if detected).

Compares two images, writes the output diff and returns the number of mismatched pixels.

## Example usage

### PIL

```python
from PIL import Image

from pixelmatch import pixelmatch

img_a = Image.open("a.png")
img_b = Image.open("b.png")
img_diff = Image.new("RGBA", img_a.size)
mismatch = pixelmatch(img_a, img_b, output=img_diff, includeAA=True)
img_diff.save("diff.png")
```

## Example output

| expected                                                                                                                                  | actual                                                                                                                                    | diff                                                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/4a.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/4a.png) | ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/4b.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/4b.png) | ![1diff](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/4diff.png) |
| ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/3a.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/3a.png) | ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/3b.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/3b.png) | ![1diff](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/3diff.png) |
| ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/6a.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/6a.png) | ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/6b.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/6b.png) | ![1diff](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/6diff.png) |
| ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/7a.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/7a.png) | ![https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/7b.png](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/7b.png) | ![1diff](https://github.com/whtsky/pixelmatch-py/raw/master/fixtures/7diff.png) |

## Changelog

### vnext

- ft: overhaul module to be more pythonic [#38](https://github.com/whtsky/pixelmatch-py/pull/36)
- ft: allow direct comparision of PIL.Image instances [#38](https://github.com/whtsky/pixelmatch-py/pull/36)

### v0.1.1

- fix: fix bug in fast path [#18](https://github.com/whtsky/pixelmatch-py/pull/18)

### v0.1.0

- Initial release
