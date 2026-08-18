import os
from PIL import Image

SRC = r"E:\Downlouds\New folder (2)"
OUT = r"E:\Desktop\SchoolPlatform\static\assistant\boy"
OUT_SIZE = 512

NAMES = {
    "calm.png": "calm.png",
    "happy.png": "happy.png",
    "sad.png": "sad.png",
    "angry.png": "angry.png",
    "amazed.png": "thinking.png",
    "wonders .png": "wonder.png",
    "factory win.png": "celebrating.png",
    "compassionate.png": "cute.png",
}

AVATAR_SRC = "hello.png"
AVATAR_OUT = r"E:\Desktop\SchoolPlatform\static\assistant\avatar_male.png"


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
            print("MISSING:", src)
            continue
        im = Image.open(src)
        im = square_crop(im)
        im = im.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
        out = os.path.join(OUT, out_name)
        im.save(out)
        print(out, "bbox", im.getbbox(), "size", im.size)

    avatar_src = os.path.join(SRC, AVATAR_SRC)
    if os.path.isfile(avatar_src):
        im = Image.open(avatar_src)
        im = square_crop(im)
        im = im.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
        im.save(AVATAR_OUT)
        print(AVATAR_OUT, "bbox", im.getbbox(), "size", im.size)
    else:
        print("MISSING avatar:", avatar_src)


if __name__ == "__main__":
    main()
