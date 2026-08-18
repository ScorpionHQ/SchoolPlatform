import os
from PIL import Image

SRC = r"E:\Downlouds"
TARGETS = ["Angry.png", "calm.png", "cute.png", "factoty .png",
           "happy.png", "sad.png", "thinking.png", "wonder.png"]

for name in TARGETS:
    path = os.path.join(SRC, name)
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()

    # alpha stats
    transparent = 0
    semi = 0
    for y in range(0, h, 7):
        for x in range(0, w, 7):
            a = px[x, y][3]
            if a == 0:
                transparent += 1
            elif a < 255:
                semi += 1
    total = (h // 7 + 1) * (w // 7 + 1)

    # corner colors
    corners = {
        "TL": px[2, 2],
        "TR": px[w - 3, 2],
        "BL": px[2, h - 3],
        "BR": px[w - 3, h - 3],
    }

    # solid background estimate: count pixels equal to TL color within tolerance
    tol = 25
    tl = px[2, 2]
    bg_like = 0
    for y in range(0, h, 7):
        for x in range(0, w, 7):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if (abs(r - tl[0]) <= tol and abs(g - tl[1]) <= tol and abs(b - tl[2]) <= tol):
                bg_like += 1

    print(f"{name}")
    print(f"  size={w}x{h}  transparent%={transparent/total*100:.1f}  semi%={semi/total*100:.1f}")
    print(f"  corners={corners}")
    print(f"  bg-like(TL)={bg_like/total*100:.1f}%")
