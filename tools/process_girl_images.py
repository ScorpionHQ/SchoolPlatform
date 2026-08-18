import os
from PIL import Image

SRC = r"E:\Downlouds"
OUT = r"E:\Desktop\SchoolPlatform\static\assistant\girl"
OUT_SIZE = 512

NAMES = {
    "Angry.png": "Angry.png",
    "calm.png": "calm.png",
    "cute.png": "cute.png",
    "factoty .png": "celebrating.png",
    "happy.png": "happy.png",
    "sad.png": "sad.png",
    "thinking.png": "thinking.png",
    "wonder.png": "wonder.png",
}


def square_crop(im):
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        return im
    im = im.crop(bbox)
    w, h = im.size
    s = max(w, h)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(im, ((s - w) // 2, (s - h) // 2))
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    for src_name, out_name in NAMES.items():
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            continue
        im = Image.open(src)
        im = square_crop(im)
        im = im.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
        out = os.path.join(OUT, out_name)
        im.save(out)
        print(out, "bbox", im.getbbox(), "size", im.size)


if __name__ == "__main__":
    main()
