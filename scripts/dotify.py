"""Turns a photo into a 1-bit stipple field: Floyd-Steinberg error diffusion
with a serpentine scan, the classic newsprint look.

Luminance is mapped to an ink *density* range rather than straight to black
and white, so dark clothing stays textured instead of collapsing into a blob.
Fully transparent pixels never take ink, which keeps the silhouette clean.
"""

from PIL import Image, ImageFilter


def _percentile(sorted_values, p):
    idx = int(round(p * (len(sorted_values) - 1)))
    return sorted_values[max(0, min(len(sorted_values) - 1, idx))]


def ink_field(image_path, cols, rows, crop=None, ink_dark=0.40, ink_light=0.05, gamma=1.0,
              sharpen=0, fade=0.0):
    """Per-cell ink probability (0..1) for a cols x rows grid.

    ink_dark and ink_light are the densities given to the darkest and the
    brightest tone. Putting the higher value on ink_light reads as light
    rather than ink: the lit side of the subject glows against the terminal
    background instead of dropping out to an empty patch.
    sharpen adds local contrast at grid resolution, so features survive the
    density drop that keeps the stipple airy.
    """
    im = Image.open(image_path).convert("RGBA")
    if crop:
        im = im.crop(crop)
    im = im.resize((cols, rows), Image.LANCZOS)
    gray_img = im.convert("L")
    if sharpen:
        gray_img = gray_img.filter(ImageFilter.UnsharpMask(radius=2, percent=sharpen, threshold=1))
    gray = gray_img.load()
    alpha = im.getchannel("A").load()

    subject = sorted(
        gray[x, y] for y in range(rows) for x in range(cols) if alpha[x, y] > 200
    )
    if not subject:
        raise ValueError("image has no opaque pixels")
    lo = _percentile(subject, 0.02)
    hi = _percentile(subject, 0.98)
    span = max(1, hi - lo)

    fade_start = rows * (1 - fade) if fade > 0 else rows
    field = []
    for y in range(rows):
        falloff = 1.0
        if y >= fade_start and rows > fade_start:
            falloff = max(0.0, 1 - (y - fade_start) / (rows - fade_start))
        row = []
        for x in range(cols):
            cover = alpha[x, y] / 255
            if cover <= 0.02:
                row.append(0.0)
                continue
            norm = min(1.0, max(0.0, (gray[x, y] - lo) / span)) ** gamma
            row.append((ink_dark + norm * (ink_light - ink_dark)) * cover * falloff)
        field.append(row)
    return field


def dither(field):
    """Serpentine Floyd-Steinberg. Returns the (x, y) cells that take ink."""
    rows, cols = len(field), len(field[0])
    buf = [row[:] for row in field]
    points = []
    for y in range(rows):
        left_to_right = y % 2 == 0
        step = 1 if left_to_right else -1
        xs = range(cols) if left_to_right else range(cols - 1, -1, -1)
        for x in xs:
            if field[y][x] <= 0:
                # outside the silhouette: drop diffused error so it can't halo
                buf[y][x] = 0.0
                continue
            value = buf[y][x]
            ink = value >= 0.5
            if ink:
                points.append((x, y))
            error = value - (1.0 if ink else 0.0)
            for dx, dy, weight in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx * step, y + dy
                if 0 <= nx < cols and 0 <= ny < rows:
                    buf[ny][nx] += error * weight
    return points


def stipple(image_path, cols, rows, **kwargs):
    return dither(ink_field(image_path, cols, rows, **kwargs))
