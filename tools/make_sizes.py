#!/usr/bin/env python3
"""Exact power-of-two downsamples of every top-level JPG in a folder.

For each source image and each target width class 2^n (default n = 8..13) the
image is box-reduced by 2^k so that every output pixel is the mean of exactly
2^k x 2^k source pixels.  To make the size divisible, one of two strategies is
used per level (never both at once):

  step    halve k times; before any halving step where a side is odd, remove
          or add (mirror-pad) one pixel on one edge of that side.
  global  one up-front crop of at most 1% of the side in total, or mirror-pad
          of at most 0.1% of the side per edge, then a single reduce by 2^k.

The cheapest feasible strategy (fewest source pixels removed + added, then
fewest added) is chosen.  Files are written as <stem>_2powNN.jpg and, at the
end, each original <stem>.jpg is renamed <stem>_native.jpg.  Re-running is safe
(existing outputs are overwritten, <stem>_native.jpg is used as the source).

The averaging itself can be done in different colour spaces (--space):

  srgb    mean of the gamma-encoded 8-bit values (fast, what most tools do)
  oklab   mean in Oklab (Ottosson 2020), a perceptual Lab-type space
  cielab  mean in CIELAB (D50)

For the Lab spaces each image is first converted from its own embedded ICC
profile (matrix/TRC RGB profiles; no profile is taken as sRGB) to linear XYZ,
averaged in strips, then converted back to the same profile.

Needs Pillow and numpy:  pip install pillow numpy
"""
import argparse
import math
import os
import re
import struct
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
DERIVED = re.compile(r"_2pow\d{2}$")
NATIVE = "_native"
STRIP_PIXELS = 4_000_000  # source pixels converted to float per strip (~100 MB working set)


# --------------------------------------------------------------------------
# Planning: which pixels to trim / pad so every output pixel is an exact block
# --------------------------------------------------------------------------

@dataclass
class Axis:
    method: str
    size: int                                   # size before adjustment
    final: int                                  # size after the full reduction
    ops: list = field(default_factory=list)     # (level, side, amount); side 0=low edge, 1=high edge
    removed: int = 0                            # source pixels removed
    added: int = 0                              # source pixels generated

    @property
    def cost(self):
        return (self.removed + self.added, self.added)


def _finish(method, size, ops):
    removed = added = 0
    for level, _side, amount in ops:
        if amount < 0:
            removed += -amount * 2**level
        else:
            added += amount * 2**level
    return Axis(method, size, 0, ops, removed, added)


def step_axis(d, k):
    """Best stepwise plan for one axis: +-1 px at each step where the size is odd."""
    best = None

    def rec(level, cur, picks):
        nonlocal best
        if level == k:
            # alternate which edge takes the pixel so the crop doesn't drift to one side
            ops = [(lv, int(i % 2 == 0), delta) for i, (lv, delta) in enumerate(picks)]
            ax = _finish("step", d, ops)
            ax.final = cur
            if best is None or ax.cost < best.cost:
                best = ax
            return
        if cur % 2 == 0:
            rec(level + 1, cur // 2, picks)
            return
        for delta in (-1, 1):
            rec(level + 1, (cur + delta) // 2, picks + [(level, delta)])

    rec(0, d, [])
    return best


def global_axis(d, k, trim_pct, pad_permille):
    """Best single up-front trim/pad for one axis, or None if the limits forbid it."""
    f = 2**k
    r = d % f
    if r == 0:
        return Axis("global", d, d // f)
    cands = []
    t = r
    if t * 100 <= d * trim_pct:
        ops = [(0, 0, -(t // 2)), (0, 1, -(t - t // 2))]
        ax = _finish("global", d, [o for o in ops if o[2]])
        ax.final = (d - t) // f
        cands.append(ax)
    p = f - r
    if -(-p // 2) * 1000 <= d * pad_permille:
        ops = [(0, 0, p // 2), (0, 1, p - p // 2)]
        ax = _finish("global", d, [o for o in ops if o[2]])
        ax.final = (d + p) // f
        cands.append(ax)
    return min(cands, key=lambda a: a.cost) if cands else None


@dataclass
class Level:
    n: int
    k: int
    method: str
    x: Axis
    y: Axis

    @property
    def size(self):
        return self.x.final, self.y.final

    @property
    def removed(self):
        return self.x.removed + self.y.removed

    @property
    def added(self):
        return self.x.added + self.y.added


def plan_levels(w, h, lo, hi, trim_pct, pad_permille):
    levels = []
    for k in range(1, 30):
        if min(w, h) // 2**k < 1:
            break
        cands = [Level(0, k, "step", step_axis(w, k), step_axis(h, k))]
        gx, gy = global_axis(w, k, trim_pct, pad_permille), global_axis(h, k, trim_pct, pad_permille)
        if gx and gy:
            cands.append(Level(0, k, "global", gx, gy))
        best = min(cands, key=lambda L: (L.removed + L.added, L.added, L.method != "global"))
        best.n = round(math.log2(best.x.final))
        if best.n < lo:
            break
        if best.n <= hi:
            levels.append(best)
    return levels


def sources(folder):
    """(source_path, base_stem, already_renamed) for each original JPG."""
    out = []
    for p in sorted(folder.glob("*.jpg")):
        if DERIVED.search(p.stem):
            continue
        renamed = p.stem.endswith(NATIVE)
        out.append((p, p.stem[: -len(NATIVE)] if renamed else p.stem, renamed))
    return out


# --------------------------------------------------------------------------
# Colour: ICC matrix/TRC profile <-> linear XYZ(D50) <-> Oklab / CIELAB
# --------------------------------------------------------------------------

D50 = np.array([0.9642, 1.0, 0.8249])
SRGB_TO_XYZ_D50 = np.array([[0.4360747, 0.3850649, 0.1430804],
                            [0.2225045, 0.7168786, 0.0606169],
                            [0.0139322, 0.0971045, 0.7141733]])
BRADFORD_D50_TO_D65 = np.array([[0.9555766, -0.0230393, 0.0631636],
                                [-0.0282895, 1.0099416, 0.0210077],
                                [0.0122982, -0.0204830, 1.3299098]])
OKLAB_M1 = np.array([[0.8189330101, 0.3618667424, -0.1288597137],   # XYZ(D65) -> LMS
                     [0.0329845436, 0.9293118715, 0.0361456387],
                     [0.0482003018, 0.2643662691, 0.6338517070]])
OKLAB_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],   # LMS' -> Lab
                     [1.9779984951, -2.4285922050, 0.4505937099],
                     [0.0259040371, 0.7827717662, -0.8086757660]])


def _srgb_trc(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def _trc_function(tag):
    """Vectorised decode curve (encoded 0..1 -> linear 0..1) from an ICC curv/para tag."""
    kind = tag[:4]
    if kind == b"curv":
        count = struct.unpack(">I", tag[8:12])[0]
        if count == 0:
            return lambda x: x
        if count == 1:
            gamma = struct.unpack(">H", tag[12:14])[0] / 256
            return lambda x: x**gamma
        table = np.frombuffer(tag[12:12 + 2 * count], dtype=">u2").astype(np.float64) / 65535
        grid = np.linspace(0, 1, count)
        return lambda x: np.interp(x, grid, table)
    if kind == b"para":
        ftype = struct.unpack(">H", tag[8:10])[0]
        n = (1, 3, 4, 5, 7)[ftype]
        g, *p = [v / 65536 for v in struct.unpack(f">{n}i", tag[12:12 + 4 * n])]
        if ftype == 0:
            return lambda x: x**g
        if ftype == 1:
            a, b = p
            return lambda x: np.where(x >= -b / a, np.maximum(a * x + b, 0) ** g, 0)
        if ftype == 2:
            a, b, c = p
            return lambda x: np.where(x >= -b / a, np.maximum(a * x + b, 0) ** g + c, c)
        if ftype == 3:
            a, b, c, d = p
            return lambda x: np.where(x >= d, np.maximum(a * x + b, 0) ** g, c * x)
        a, b, c, d, e, f = p
        return lambda x: np.where(x >= d, np.maximum(a * x + b, 0) ** g + e, c * x + f)
    raise ValueError(f"unsupported ICC curve type {kind!r}")


def read_profile(icc):
    """-> (3x3 linear RGB -> XYZ D50, [three decode functions]); None means sRGB."""
    if icc is None:
        return SRGB_TO_XYZ_D50, [_srgb_trc] * 3
    count = struct.unpack(">I", icc[128:132])[0]
    tags = {}
    for i in range(count):
        sig, off, size = struct.unpack(">4sII", icc[132 + 12 * i:144 + 12 * i])
        tags[sig] = icc[off:off + size]
    try:
        cols = [struct.unpack(">3i", tags[s][8:20]) for s in (b"rXYZ", b"gXYZ", b"bXYZ")]
        curves = [_trc_function(tags[s]) for s in (b"rTRC", b"gTRC", b"bTRC")]
    except KeyError as e:
        raise ValueError(f"ICC profile is not a matrix/TRC RGB profile (missing {e})") from None
    return np.array(cols, dtype=np.float64).T / 65536, curves


class Space:
    """Per-image conversion between 8-bit RGB (in its own profile) and a Lab space."""

    def __init__(self, name, icc):
        rgb_to_xyz, curves = read_profile(icc)
        self.name = name
        self.dec = [fn(np.arange(256) / 255).astype(np.float32) for fn in curves]
        grid = np.linspace(0, 1, 1 << 16)
        self.enc = []
        for fn in curves:
            lin = np.maximum.accumulate(fn(grid))
            self.enc.append(lambda v, lin=lin: np.interp(np.clip(v, 0, 1), lin, grid))
        if name == "oklab":
            a = OKLAB_M1 @ BRADFORD_D50_TO_D65 @ rgb_to_xyz
            self._fwd = (a.T.astype(np.float32), OKLAB_M2.T.astype(np.float32))
            self._inv = (np.linalg.inv(OKLAB_M2).T.astype(np.float32), np.linalg.inv(a).T.astype(np.float32))
        elif name == "cielab":
            self._fwd = (rgb_to_xyz.T.astype(np.float32),)
            self._inv = (np.linalg.inv(rgb_to_xyz).T.astype(np.float32),)
        else:
            raise ValueError(name)

    def to_lab(self, rgb8):
        lin = np.empty(rgb8.shape, np.float32)
        for c in range(3):
            lin[..., c] = self.dec[c][rgb8[..., c]]
        flat = lin.reshape(-1, 3)
        if self.name == "oklab":
            a_t, m2_t = self._fwd
            lab = np.cbrt(flat @ a_t) @ m2_t
        else:
            xyz = (flat @ self._fwd[0]) / D50.astype(np.float32)
            d = 6 / 29
            f = np.where(xyz > d**3, np.cbrt(xyz), xyz / (3 * d * d) + 4 / 29)
            lab = np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1)
        return lab.reshape(rgb8.shape).astype(np.float32)

    def from_lab(self, lab):
        flat = lab.reshape(-1, 3).astype(np.float64)
        if self.name == "oklab":
            m2i_t, ai_t = self._inv
            lin = (flat @ m2i_t.astype(np.float64)) ** 3 @ ai_t.astype(np.float64)
        else:
            fy = (flat[:, 0] + 16) / 116
            f = np.stack([fy + flat[:, 1] / 500, fy, fy - flat[:, 2] / 200], axis=1)
            d = 6 / 29
            xyz = np.where(f > d, f**3, 3 * d * d * (f - 4 / 29)) * D50
            lin = xyz @ self._inv[0].astype(np.float64)
        out = np.empty(lin.shape, np.uint8)
        for c in range(3):
            out[:, c] = np.rint(self.enc[c](lin[:, c]) * 255)
        return out.reshape(lab.shape)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def edges(axis, level):
    lo_c = lo_p = hi_c = hi_p = 0
    for lv, side, amount in axis.ops:
        if lv != level:
            continue
        if amount < 0:
            lo_c, hi_c = (lo_c - amount, hi_c) if side == 0 else (lo_c, hi_c - amount)
        else:
            lo_p, hi_p = (lo_p + amount, hi_p) if side == 0 else (lo_p, hi_p + amount)
    return lo_c, hi_c, lo_p, hi_p


def adjust(im, ax, ay, level):
    """Crop / mirror-pad a PIL image."""
    xlc, xhc, xlp, xhp = edges(ax, level)
    ylc, yhc, ylp, yhp = edges(ay, level)
    if xlc or xhc or ylc or yhc:
        im = im.crop((xlc, ylc, im.width - xhc, im.height - yhc))
    if not (xlp or xhp or ylp or yhp):
        return im
    w, h = im.size
    out = Image.new(im.mode, (w + xlp + xhp, h + ylp + yhp))
    out.paste(im, (xlp, ylp))
    if xlp:
        out.paste(im.crop((0, 0, xlp, h)).transpose(Image.FLIP_LEFT_RIGHT), (0, ylp))
    if xhp:
        out.paste(im.crop((w - xhp, 0, w, h)).transpose(Image.FLIP_LEFT_RIGHT), (xlp + w, ylp))
    if ylp:
        out.paste(out.crop((0, ylp, out.width, 2 * ylp)).transpose(Image.FLIP_TOP_BOTTOM), (0, 0))
    if yhp:
        out.paste(
            out.crop((0, ylp + h - yhp, out.width, ylp + h)).transpose(Image.FLIP_TOP_BOTTOM),
            (0, ylp + h),
        )
    return out


def adjust_array(arr, ax, ay, level):
    """Same as adjust() for an (H, W, 3) float array."""
    xlc, xhc, xlp, xhp = edges(ax, level)
    ylc, yhc, ylp, yhp = edges(ay, level)
    if xlc or xhc or ylc or yhc:
        arr = arr[ylc:arr.shape[0] - yhc, xlc:arr.shape[1] - xhc]
    if xlp or xhp or ylp or yhp:
        arr = np.pad(arr, ((ylp, yhp), (xlp, xhp), (0, 0)), mode="symmetric")
    return arr


def reduce_lab(im, f, space):
    """Mean of exact f x f blocks of a PIL RGB image, taken in the Lab space, in strips."""
    w, h = im.size
    out = np.empty((h // f, w // f, 3), np.float32)
    rows = f * max(1, STRIP_PIXELS // (f * w))
    for y in range(0, h, rows):
        y1 = min(y + rows, h)
        lab = space.to_lab(np.asarray(im.crop((0, y, w, y1))))
        out[y // f:y1 // f] = lab.reshape((y1 - y) // f, f, w // f, f, 3).mean(axis=(1, 3))
    return out


def mean2(arr):
    h, w = arr.shape[:2]
    return arr.reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))


def render(im, L, space=None):
    if space is None:  # average the gamma-encoded values
        cur = im
        if L.method == "global":
            cur = adjust(cur, L.x, L.y, 0).reduce(2**L.k)
        else:
            for level in range(L.k):
                cur = adjust(cur, L.x, L.y, level).reduce(2)
        assert cur.size == L.size, (cur.size, L.size)
        return cur
    if L.method == "global":
        arr = reduce_lab(adjust(im, L.x, L.y, 0), 2**L.k, space)
    else:
        arr = reduce_lab(adjust(im, L.x, L.y, 0), 2, space)
        for level in range(1, L.k):
            arr = mean2(adjust_array(arr, L.x, L.y, level))
    out = Image.fromarray(space.from_lab(arr), "RGB")
    assert out.size == L.size, (out.size, L.size)
    return out


def process(path, base, levels, quality, space_name):
    folder = path.parent
    im = Image.open(path)
    icc = im.info.get("icc_profile")
    im.load()
    space = None if space_name == "srgb" else Space(space_name, icc)
    done = []
    for L in levels:
        dest = folder / f"{base}_2pow{L.n:02d}.jpg"
        tmp = dest.with_name(dest.name + ".tmp")
        out = render(im, L, space)
        out.save(tmp, "JPEG", quality=quality, subsampling=0, optimize=True,
                 progressive=True, icc_profile=icc)
        os.replace(tmp, dest)
        done.append((dest.name, out.size))
    return path, done


def describe(L):
    return (f"2^{L.n:<2} k={L.k:<2} {L.method:<6} -> {L.size[0]:>5}x{L.size[1]:<5} "
            f"removed {L.x.removed:>3}+{L.y.removed:<3} added {L.x.added:>3}+{L.y.added:<3} (src px, w+h)")


def main():
    default_dir = Path(__file__).resolve().parent.parent / "img"
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=default_dir, help="folder with the source JPGs (default: ../img)")
    ap.add_argument("--space", choices=("srgb", "oklab", "cielab"), default="srgb",
                    help="colour space the block averaging is done in")
    ap.add_argument("--plan", action="store_true", help="print the plan and exit without writing")
    ap.add_argument("--jobs", type=int, default=os.cpu_count(), help="parallel worker processes")
    ap.add_argument("--quality", type=int, default=90, help="JPEG quality of the outputs")
    ap.add_argument("--min-n", type=int, default=8)
    ap.add_argument("--max-n", type=int, default=13)
    ap.add_argument("--trim-pct", type=int, default=1, help="max global trim, %% of a side (total)")
    ap.add_argument("--pad-permille", type=int, default=1, help="max global pad, per mille of a side per edge")
    ap.add_argument("--no-rename", action="store_true", help="do not append _native to the originals")
    args = ap.parse_args()

    jobs = []
    for path, base, renamed in sources(args.dir):
        with Image.open(path) as im:
            w, h = im.size
        levels = plan_levels(w, h, args.min_n, args.max_n, args.trim_pct, args.pad_permille)
        jobs.append((path, base, renamed, w, h, levels))

    for path, base, renamed, w, h, levels in jobs:
        print(f"{path.name}  {w}x{h}")
        for L in levels:
            print("   " + describe(L))
    total = sum(len(j[5]) for j in jobs)
    print(f"\n{len(jobs)} sources, {total} downsampled files, "
          f"{sum(L.added > 0 for j in jobs for L in j[5])} levels with generated pixels, averaging in {args.space}")
    if args.plan:
        return 0

    work = sorted(jobs, key=lambda j: -j[3] * j[4])
    failed = []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(process, p, b, lv, args.quality, args.space): (p, lv)
                for p, b, _r, _w, _h, lv in work}
        for fut in as_completed(futs):
            p, lv = futs[fut]
            try:
                fut.result()
                print(f"done {p.name} ({len(lv)} files)", flush=True)
            except Exception as e:  # keep going; the original stays untouched
                failed.append(p)
                print(f"FAILED {p.name}: {e!r}", file=sys.stderr, flush=True)

    if not args.no_rename:
        for path, base, renamed, *_ in jobs:
            if path in failed or renamed:
                continue
            os.rename(path, path.with_name(base + NATIVE + ".jpg"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
