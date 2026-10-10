"""Image loading that is safe for medical PNGs. No torch dependency."""
import numpy as np
from PIL import Image


def to_rgb(img: Image.Image) -> Image.Image:
    """Grayscale-as-RGB for any input mode, including 16-bit and float images.

    PIL's convert("L") clips 16-bit values above 255 to white, which silently turns
    many 16-bit X-ray PNGs into blank images. High bit-depth images are min-max
    scaled to 0-255 first.
    """
    if img.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        a = np.asarray(img, dtype=np.float64)
        lo, hi = float(a.min()), float(a.max())
        a = (a - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(a)
        img = Image.fromarray(a.round().astype(np.uint8), mode="L")
    return img.convert("L").convert("RGB")


def load_image(path) -> Image.Image:
    with Image.open(path) as im:
        return to_rgb(im)
