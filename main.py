from __future__ import annotations

import argparse
from PIL import Image, ImageDraw
from pathlib import Path
from typing import TYPE_CHECKING

from beatmap import Beatmap

if TYPE_CHECKING:
    from beatmap import HitObject


def _get_hitobjects(times: tuple[int, int], hitobjects: list[HitObject]) -> list[HitObject]:
    r = []

    for hitobject in hitobjects:
        if hitobject.time >= times[0] and hitobject.time <= times[1]:
            r.append(hitobject)

    return r

def _calculate_radius(cs: float, ez=False, hr=False) -> float:
    if ez:
        cs /= 2
    elif hr:
        cs *= 1.3

        if cs > 10:
            cs = 10

    return 54.4 - 4.48 * cs

def _flip_hitobjects(hitobjects: list[HitObject]) -> list[HitObject]:
    r = []

    for hitobject in hitobjects:
        hitobject.y = 384 - hitobject.y
        r.append(hitobject)

    return r

def _parse_editor_timestamp(timestamp: str) -> int:
    minutes, seconds, miliseconds = timestamp.split(":")
    minutes, seconds, miliseconds = int(minutes), int(seconds), int(miliseconds)

    seconds += minutes * 60
    miliseconds += seconds * 1000

    return miliseconds

def _draw_object(d: ImageDraw.ImageDraw,
                 hitobject: HitObject,
                 radius: float,
                 m: int,
                 outline_width: int,
                 outline: tuple[int, int, int],
                 fill: tuple[int, int, int],
                 offset: tuple[int, int]=(0, 0)):
    radius *= m
    editor_res = (512 * m, 384 * m)
    hitobject_res = (640 * m, 480 * m)
    deviation = hitobject_res[0] - editor_res[0], hitobject_res[1] - editor_res[1]

    x, y = hitobject.x * m, hitobject.y * m
    x, y = x + deviation[0] // 2, y + deviation[1] // 2
    x, y = x + offset[0], y + offset[1]

    pos = (int(x - radius), int(y - radius), int(x + radius), int(y + radius))
    d.ellipse(pos, fill=fill, outline=outline, width=outline_width)

def _resize(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    factor = size[1] / img.height

    img = img.resize((int(img.width * factor), int(img.height * factor)))
    missing_width = size[0] - img.width # total, divide by 2 to get offset

    r_img = Image.new("RGBA", size)
    r_img.alpha_composite(img, (0 + missing_width // 2, 0))

    return r_img

def _tuple(s: str) -> tuple:
    nums = s.split(",")
    l = []

    for n in nums:
        l.append(int(n))

    return tuple(l)

def _check_tuple(t: tuple | None, expected_len: int, arg_name: str) -> None:
    if t and len(t) != expected_len:
        exit(f"fatal: {arg_name} expected {expected_len} values")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("times", nargs=2)
    parser.add_argument("-m", "--map", required=True, type=Path)

    parser.add_argument("-r", "--resolution", type=_tuple, default=(1920, 1080))
    parser.add_argument("-f", "--fill", type=_tuple, default=None)
    parser.add_argument("-o", "--outline", type=_tuple, default=None)
    parser.add_argument("-ow", "--outline-width", type=int, default=3)

    parser.add_argument("-ez", action="store_true")
    parser.add_argument("-hr", action="store_true")
    args = parser.parse_args()

    if args.ez and args.hr:
        return

    assert args.map.exists()

    _check_tuple(args.outline, 3, "--outline")
    _check_tuple(args.fill, 3, "--fill")
    _check_tuple(args.resolution, 2, "--resolution")

    if not args.times[0].isdigit():
        args.times[0] = _parse_editor_timestamp(args.times[0])
    if not args.times[1].isdigit():
        args.times[1] = _parse_editor_timestamp(args.times[1])

    beatmap = Beatmap.from_path(args.map)

    hitobjects = _get_hitobjects(args.times, beatmap.hitobjects)
    radius = _calculate_radius(beatmap.difficulty.CircleSize, args.ez, args.hr)

    if args.hr:
        hitobjects = _flip_hitobjects(hitobjects)

    target_res = args.resolution

    m = 4
    scale = target_res[1] / 768
    resize_res = (int(target_res[0] / scale), int(target_res[1] / scale))

    hitobject_res = (640 * m, 480 * m)

    circle_overlay = Image.new("RGBA", hitobject_res)
    d = ImageDraw.Draw(circle_overlay)

    for hitobject in hitobjects:
        _draw_object(d, hitobject, radius, m, outline_width=args.outline_width, outline=args.outline, fill=args.fill, offset=(1, 16))

    circle_overlay = _resize(circle_overlay, resize_res)
    circle_overlay.save("scorebar-bg.png")


if __name__ == "__main__":
    main()
