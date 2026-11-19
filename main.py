#!/usr/bin/env python3
"""news-image-20261118: sum up Wednesday 18 November 2026's world news
in one 1024x1024 PNG front page, drawn with the Python standard library
only (no network, no fonts on disk: a built-in 5x7 bitmap font).

Stories (all reported on 18 Nov 2026):
  LEAD  Xi Jinping and Vladimir Putin meet in Shenzhen; Donald Trump
        joins them for a three-way summit on Thursday.
  GULF  Iran launches drones at Kuwait and Bahrain after US aircraft
        struck a missile site on Qeshm Island.
  UKRAINE  Ukraine hits the Kerch Bridge again; part of the road
        span collapses.
  AMERICA  Mary Peltola wins Alaska's Senate seat; Democrats take
        a 56-44 Senate majority.
  ISRAEL  Matan Kahana is elected Knesset speaker; Trump's Board of
        Peace faults Israel and Hamas over the Gaza ceasefire.
  HEALTH  Ebola in DR Congo passes 11,000 cases; the US loses its
        measles-free status after 26 years.
  MARKETS  Nvidia posts a record $115.8bn quarter; Anthropic prices
        its IPO; the Fed releases its meeting minutes.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (17, 24, 39)
NAVY = (15, 42, 74)
NAVY2 = (23, 64, 110)
GOLD = (212, 175, 55)
RED = (178, 34, 34)
TEAL = (14, 116, 110)
GREY = (90, 96, 108)
LIGHT = (226, 232, 240)
WHITE = (255, 255, 255)
SKY = (186, 214, 235)
GREEN = (22, 120, 60)

# ---------------------------------------------------------------- canvas
px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def fill(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = c


def rect(x, y, w, h, c, t=1):
    fill(x, y, w, t, c)
    fill(x, y + h - t, w, t, c)
    fill(x, y, t, h, c)
    fill(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        for a in range(t):
            for b in range(t):
                set_px(x0 + a, y0 + b, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_px(xx, yy, c)


def ring(cx, cy, r, c, t=3):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
            if r - t <= d <= r + t:
                set_px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    xs = [x0, x1, x2]
    ys = [y0, y1, y2]
    for yy in range(min(ys), max(ys) + 1):
        xs_at = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                (x2, y2, x0, y0)):
            if ay == by:
                continue
            if min(ay, by) <= yy <= max(ay, by):
                xs_at.append(ax + (yy - ay) * (bx - ax) / (by - ay))
        if len(xs_at) >= 2:
            for xx in range(int(min(xs_at)), int(max(xs_at)) + 1):
                set_px(xx, yy, c)


def star(cx, cy, r, c):
    # 8-point starburst
    for k in range(8):
        ang = k * 3.14159265 / 4
        x1 = int(cx + r * 0.95 * __import__("math").cos(ang))
        y1 = int(cy + r * 0.95 * __import__("math").sin(ang))
        line(cx, cy, x1, y1, c, 3)
    disc(cx, cy, max(3, r // 3), c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '1' = ink.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}


def text_w(s, scale):
    return len(s) * (6 * scale) - scale


def draw_text(x, y, s, scale, c):
    s = s.upper()
    cx = x
    for ch in s:
        g = GLYPHS.get(ch, GLYPHS["?"])
        for r, row in enumerate(g):
            for col, bit in enumerate(row):
                if bit == "1":
                    fill(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def draw_center(x, y, w, s, scale, c):
    draw_text(x + (w - text_w(s, scale)) // 2, y, s, scale, c)


def wrap(s, scale, max_w):
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(x, y, s, scale, max_w, c, lh=None):
    lh = lh or (7 * scale + 4)
    for ln in wrap(s, scale, max_w):
        draw_text(x, y, ln, scale, c)
        y += lh
    return y


# ---------------------------------------------------------------- layout
fill(0, 0, W, H, PAPER)

# Masthead
fill(0, 0, W, 118, NAVY)
fill(0, 118, W, 6, GOLD)
draw_center(0, 18, W, "THE WORLD IN ONE PICTURE", 6, WHITE)
draw_center(0, 74, W, "WEDNESDAY  18  NOVEMBER  2026", 3, GOLD)

# Lead story ------------------------------------------------------------
LY, LH = 140, 300
fill(24, LY, 976, LH, WHITE)
rect(24, LY, 976, LH, INK, 2)
# lead illustration: Shenzhen skyline + summit table (right half)
LX = 560
fill(LX, LY + 2, 438, LH - 4, SKY)
for bx, bw, bh in ((576, 46, 62), (630, 36, 92), (674, 52, 52),
                   (734, 34, 80), (776, 44, 58), (828, 38, 96),
                   (874, 48, 68), (930, 40, 48)):
    fill(bx, LY + 196 - bh, bw, bh, NAVY2)
    fill(bx, LY + 196 - bh, bw, 6, GOLD)
# three leaders at the table
for cx, suit, flag in ((640, RED, (200, 30, 30)),
                       (760, NAVY, (30, 60, 160)),
                       (880, (40, 90, 60), (180, 30, 30))):
    disc(cx, LY + 222, 22, (232, 196, 160))          # head
    fill(cx - 26, LY + 244, 52, 44, suit)            # shoulders
    fill(cx - 26, LY + 244, 52, 8, WHITE)            # collar
    fill(cx - 14, LY + 198, 28, 12, flag)            # flag pin
fill(580, LY + 288, 400, 10, (120, 72, 20))          # table
fill(580, LY + 298, 400, 2, (90, 52, 14))
# lead text (left half)
draw_text(44, LY + 22, "LEAD STORY", 2, RED)
draw_text(44, LY + 52, "XI AND PUTIN", 4, INK)
draw_text(44, LY + 92, "MEET IN", 4, INK)
draw_text(44, LY + 132, "SHENZHEN", 4, INK)
draw_block(44, LY + 182, "Trump joins them on Thursday for a "
           "three-way summit on Ukraine, Iran and trade.", 2, 480, INK)
draw_text(44, LY + 262, "APEC SUMMIT OPENS IN CHINA", 2, GREY)

# Story panels ----------------------------------------------------------
def panel(x, y, w, h, kicker, kcolor, pic, headline, body):
    fill(x, y, w, h, WHITE)
    rect(x, y, w, h, INK, 2)
    fill(x, y, w, 34, kcolor)
    draw_text(x + 12, y + 8, kicker, 2, WHITE)
    pic(x, y + 34, w)
    yy = y + 34 + 92
    for ln in headline:
        draw_text(x + 14, yy, ln, 3, INK)
        yy += 26
    draw_block(x + 14, yy + 2, body, 2, w - 28, INK, lh=17)


def pic_gulf(x, y, w):
    fill(x, y, w, 92, (10, 30, 60))
    fill(x, y + 64, w, 28, (16, 60, 110))
    # drones
    for cx, cy in ((x + 70, y + 30), (x + 160, y + 20), (x + 240, y + 36)):
        disc(cx, cy, 5, WHITE)
        line(cx - 14, cy - 8, cx + 14, cy + 8, WHITE, 2)
        line(cx - 14, cy + 8, cx + 14, cy - 8, WHITE, 2)
    star(x + 250, y + 70, 14, GOLD)
    draw_text(x + 14, y + 72, "GULF", 2, GOLD)


def pic_bridge(x, y, w):
    fill(x, y, w, 92, SKY)
    fill(x, y + 62, w, 30, (70, 110, 150))
    fill(x + 40, y + 14, 12, 48, INK)
    fill(x + w - 52, y + 14, 12, 48, INK)
    line(x + 46, y + 16, x + w - 46, y + 16, INK, 3)
    # deck, broken in the middle
    fill(x + 10, y + 54, w // 2 - 34, 8, RED)
    fill(x + w // 2 + 24, y + 54, w // 2 - 34, 8, RED)
    tri(x + w // 2 - 26, y + 62, x + w // 2 - 6, y + 62,
        x + w // 2 - 16, y + 84, (60, 60, 60))
    disc(x + w // 2 + 8, y + 34, 11, (120, 120, 120))
    disc(x + w // 2 + 22, y + 26, 14, (150, 150, 150))


def pic_senate(x, y, w):
    fill(x, y, w, 92, (230, 228, 215))
    line(x + w // 2, y + 6, x + w // 2, y + 22, NAVY, 2)
    fill(x + w // 2, y + 6, 16, 9, RED)
    disc(x + w // 2, y + 52, 32, NAVY)
    fill(x + w // 2 - 32, y + 52, 64, 8, NAVY)
    for cx in range(x + w // 2 - 26, x + w // 2 + 27, 13):
        fill(cx, y + 60, 6, 24, NAVY)
    fill(x + w // 2 - 42, y + 84, 84, 8, NAVY)
    fill(x + 24, y + 14, 58, 66, RED)
    fill(x + 30, y + 20, 46, 54, WHITE)
    draw_text(x + 36, y + 36, "56", 3, RED)
    draw_text(x + 36, y + 60, "44", 2, INK)


def pic_israel(x, y, w):
    fill(x, y, w, 92, (238, 240, 244))
    fill(x + 20, y + 26, w - 40, 10, NAVY)
    for cx in range(x + 34, x + w - 30, 34):
        fill(cx, y + 36, 10, 40, NAVY)
    fill(x + 20, y + 76, w - 40, 10, NAVY)
    # flag: blue stripes, star of david
    fill(x + w - 96, y + 14, 76, 44, WHITE)
    rect(x + w - 96, y + 14, 76, 44, NAVY, 2)
    fill(x + w - 96, y + 20, 76, 5, NAVY)
    fill(x + w - 96, y + 47, 76, 5, NAVY)
    tri(x + w - 72, y + 26, x + w - 48, y + 26, x + w - 60, y + 48, NAVY)
    tri(x + w - 72, y + 48, x + w - 48, y + 48, x + w - 60, y + 26, NAVY)


def pic_health(x, y, w):
    fill(x, y, w, 92, (250, 235, 235))
    disc(x + 70, y + 46, 32, RED)
    fill(x + 63, y + 24, 14, 44, WHITE)
    fill(x + 48, y + 39, 44, 14, WHITE)
    # virus
    cx, cy = x + w - 80, y + 46
    disc(cx, cy, 26, (120, 30, 90))
    for k in range(8):
        import math
        a = k * math.pi / 4
        line(cx, cy, int(cx + 36 * math.cos(a)),
             int(cy + 36 * math.sin(a)), (120, 30, 90), 3)
    disc(cx, cy, 26, (120, 30, 90))
    disc(cx - 8, cy - 6, 5, WHITE)
    disc(cx + 8, cy + 8, 4, WHITE)


def pic_markets(x, y, w):
    fill(x, y, w, 108, (232, 245, 232))
    line(x + 16, y + 88, x + 70, y + 62, GREEN, 4)
    line(x + 70, y + 62, x + 120, y + 70, GREEN, 4)
    line(x + 120, y + 70, x + 180, y + 38, GREEN, 4)
    line(x + 180, y + 38, x + w - 24, y + 16, GREEN, 4)
    tri(x + w - 24, y + 16, x + w - 44, y + 16, x + w - 24, y + 36, GREEN)
    fill(x + 20, y + 14, 66, 30, INK)
    draw_text(x + 28, y + 22, "NVDA", 2, GOLD)


PW, PH = 314, 252
PY1, PY2 = 456, 724
PX = (24, 355, 686)

panel(PX[0], PY1, PW, PH, "THE GULF", RED, pic_gulf,
      ["IRAN STRIKES", "AT THE GULF"],
      "Drones hit Kuwait and Bahrain after US jets hit Qeshm Island.")
panel(PX[1], PY1, PW, PH, "UKRAINE", NAVY2, pic_bridge,
      ["KERCH BRIDGE", "HIT AGAIN"],
      "Ukraine hits the bridge to Crimea again; part of the road span falls.")
panel(PX[2], PY1, PW, PH, "AMERICA", TEAL, pic_senate,
      ["PELTOLA WINS", "ALASKA"],
      "Peltola beats Dan Sullivan. Democrats take the Senate, 56-44.")
panel(PX[0], PY2, PW, PH, "ISRAEL", NAVY, pic_israel,
      ["KAHANA TAKES", "THE SPEAKER"],
      "Kahana is elected speaker. Trump's Board of Peace faults both sides.")
panel(PX[1], PY2, PW, PH, "HEALTH", RED, pic_health,
      ["EBOLA PASSES", "11,000 CASES"],
      "DR Congo's Ebola passes 11,000 cases. The US loses measles-free status.")
panel(PX[2], PY2, PW, PH, "MARKETS", GREEN, pic_markets,
      ["NVIDIA'S", "RECORD DAY"],
      "Nvidia posts a record $115.8bn quarter. Anthropic prices its IPO.")

# Footer
fill(0, 992, W, 32, NAVY)
draw_center(0, 1000, W, "18 NOVEMBER 2026  -  THE DAY'S WORLD NEWS IN ONE IMAGE", 2, WHITE)

# ---------------------------------------------------------------- PNG out
def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3])
               for y in range(H))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))

outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(outdir, exist_ok=True)
path = os.path.join(outdir, "entry.png")
with open(path, "wb") as f:
    f.write(png)
print("wrote", path, len(png), "bytes")
