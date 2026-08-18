import os
from PIL import Image, ImageDraw

SRC = r"E:\Downlouds"
OUT = r"E:\Desktop\SchoolPlatform\static\assistant\girl"
NAMES = ["Angry", "calm", "cute", "factoty ", "happy", "sad", "thinking", "wonder"]
PREVIEW = r"E:\Downlouds\preview_girl_states.png"

TILE = 12
CELL = 512


def checkerboard(size):
    im = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(im)
    t = TILE
    for y in range(0, size, t):
        for x in range(0, size, t):
            if (x // t + y // t) % 2 == 0:
                d.rectangle([x, y, x + t - 1, y + t - 1], fill=(200, 200, 200))
    return im


rows = (len(NAMES) + 3) // 4
W = 4 * (CELL + 12) + 24
H = rows * (CELL + 90) + 30
canvas = Image.new("RGB", (W, H), (30, 30, 40))
d = ImageDraw.Draw(canvas)

for i, name in enumerate(NAMES):
    col = i % 4
    row = i // 4
    x0 = 12 + col * (CELL + 12)
    y0 = 12 + row * (CELL + 90)

    orig = Image.open(os.path.join(SRC, name + ".png")).convert("RGB")
    orig.thumbnail((CELL, CELL), Image.LANCZOS)
    orig = orig.convert("RGB")

    proc = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    cb = checkerboard(CELL)
    cb.paste(proc, (0, 0), proc)
    cb = cb.convert("RGB")

    # label
    d.text((x0, y0 + CELL + 8), name.strip() or "(unnamed)", fill=(255, 255, 255))

    # place original left half, processed right half
    half = CELL // 2
    combo = Image.new("RGB", (CELL, CELL), (0, 0, 0))
    combo.paste(orig.crop((0, 0, half, CELL)), (0, 0))
    combo.paste(cb.crop((half, 0, CELL, CELL)), (half, 0))
    canvas.paste(combo, (x0, y0))

canvas.save(PREVIEW)
print(PREVIEW)
