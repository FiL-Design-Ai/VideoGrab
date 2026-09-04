"""Одноразовый генератор иконки приложения: синий градиентный квадрат со стрелкой вниз."""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
TOP = (47, 126, 247)
BOTTOM = (31, 209, 255)


def make(size: int) -> Image.Image:
    u = size / 16

    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / (size - 1)
        c = tuple(int(a + (b - a) * t) for a, b in zip(TOP, BOTTOM))
        gd.line([(0, y), (size, y)], fill=c + (255,))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255
    )

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    d.rounded_rectangle([6.6 * u, 3.2 * u, 9.4 * u, 9.2 * u], radius=1.1 * u, fill=white)
    d.polygon([(3.4 * u, 8.4 * u), (12.6 * u, 8.4 * u), (8.0 * u, 13.8 * u)], fill=white)
    return img


def main():
    out = Path(__file__).resolve().parent / "assets" / "icon.ico"
    out.parent.mkdir(parents=True, exist_ok=True)
    img = make(SIZE)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    img.save(out, sizes=[(s, s) for s in sizes])
    print(f"saved {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
