import numpy as np
from PIL import Image

from src.imaging import load_image, to_rgb


def test_16bit_png_is_scaled_not_clipped(tmp_path):
    a = np.linspace(0, 4095, 64 * 64).reshape(64, 64).astype(np.uint16)  # 12-bit range, typical for X-rays
    path = tmp_path / "x16.png"
    Image.fromarray(a).save(path)
    img = load_image(path)
    arr = np.asarray(img)
    assert img.mode == "RGB" and arr.shape == (64, 64, 3)
    assert arr.min() == 0 and arr.max() == 255
    assert (arr[..., 0] < 250).mean() > 0.9   # plain convert("L") would make almost all of it white


def test_8bit_and_rgba_pass_through():
    g = Image.fromarray(np.full((8, 8), 77, np.uint8))
    assert np.asarray(to_rgb(g))[0, 0].tolist() == [77, 77, 77]
    rgba = Image.new("RGBA", (8, 8), (10, 10, 10, 255))
    assert to_rgb(rgba).mode == "RGB"


def test_constant_16bit_image_does_not_divide_by_zero():
    flat = Image.fromarray(np.full((8, 8), 1000, np.uint16))
    assert np.asarray(to_rgb(flat)).max() == 0
