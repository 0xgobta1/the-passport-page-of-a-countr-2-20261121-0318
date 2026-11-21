#!/usr/bin/env python3
"""Draw the Auroria passport spread (entry.png) for the make.fun bounty
"The Passport Page of a Country That Isn't There".

The image is drawn procedurally with Pillow: an open passport spread for
the fictional Republic of Auroria, an Arctic island nation. Left page: the
data page (bilingual Aurorian/English, drawn portrait, ICAO MRZ with real
check digits). Right page: a Norwegian Schengen visa plus six border
stamps in strict chronological order after the date of issue, and a
"Dark Months" travel endorsement that says what kind of place Auroria is.

Deterministic: no randomness, no network, fixed geometry. Run:
    python3 draw.py            # writes entry.png beside this file
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF = os.path.join(FONT_DIR, "DejaVuSerif.ttf")
SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
MONO_B = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")

W, H = 1024, 1024

NAVY = (29, 58, 95)
NAVY_D = (22, 42, 68)
INK = (22, 40, 58)
GOLD = (176, 141, 60)
GOLD_L = (201, 168, 92)
CREAM = (245, 239, 221)
CREAM_D = (238, 230, 205)
LABEL = (90, 106, 122)
DESK = (38, 48, 60)

# ---------------------------------------------------------------- dates
# Passport issued 12 MAR 2023, expires 12 MAR 2033. Every stamp is dated
# after the issue date, in chronological order, and the visa's validity
# covers the Bergen trip. Holder born 14 JUN 1994 in Skardvik.
ISSUE = "12 MAR 2023"
EXPIRY = "12 MAR 2033"


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked(draw, xy, text, fnt, fill, tracking=2):
    """Draw text with extra space between characters (letterspaced caps)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def centered(draw, cx, y, text, fnt, fill, tracking=0):
    if tracking:
        total = sum(draw.textlength(c, font=fnt) + tracking for c in text) - tracking
        tracked(draw, (cx - total / 2, y), text, fnt, fill, tracking)
    else:
        draw.text((cx - draw.textlength(text, font=fnt) / 2, y), text,
                  font=fnt, fill=fill)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- MRZ
def mrz_check(data):
    """ICAO Doc 9303 check digit: weights 7,3,1; A=10..Z=35, '<'=0."""
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(data):
        if ch == "<":
            v = 0
        elif ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - 55  # A=10
        total += v * weights[i % 3]
    return str(total % 10)


def transliterate(text):
    return (text.replace("Ó", "O").replace("Ú", "U").replace("Í", "I")
                .replace("Ð", "D").replace("Þ", "TH").replace("Á", "A")
                .replace("É", "E").replace("Ö", "O").replace("Ä", "A"))


def build_mrz():
    surname = transliterate("HALLDÓRSDÓTTIR")
    given = transliterate("SIGRÚN ELÍN").replace(" ", "<")
    line1 = ("P<AUR" + surname + "<<" + given).ljust(44, "<")
    assert len(line1) == 44, len(line1)
    doc_no = "AUR847291"
    dob = "940614"
    exp = "330312"
    personal = "1406943821".ljust(15, "<")
    line2 = (doc_no + mrz_check(doc_no) + "AUR" + dob + mrz_check(dob)
             + "F" + exp + mrz_check(exp) + personal)
    composite = mrz_check(line2[0:10] + line2[13:20] + line2[21:43])
    line2 += composite
    assert len(line2) == 44, len(line2)
    return line1, line2


# ------------------------------------------------------------- guilloche
def guilloche(page, x0, y0, x1, y1, color, alpha=26, step=46, amp=5):
    """Faint wavy security lines across a page."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    y = y0 + 8
    while y < y1 - 4:
        pts = []
        x = x0
        while x <= x1:
            pts.append((x, y + amp * math.sin((x - x0) / 38.0)))
            x += 6
        d.line(pts, fill=color + (alpha,), width=1)
        y += step
    page.alpha_composite(ov)


def watermark(page, x0, y0, x1, y1, text):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = font(SERIF_B, 92)
    layer = Image.new("RGBA", (520, 130), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((8, 10), text, font=f, fill=NAVY + (11,))
    layer = layer.rotate(-27, expand=True, resample=Image.BICUBIC)
    ov.alpha_composite(layer, ((x0 + x1) // 2 - layer.width // 2,
                               (y0 + y1) // 2 - layer.height // 2))
    page.alpha_composite(ov)


# ----------------------------------------------------------------- arms
def coat_of_arms(d, cx, cy, r):
    """Aurora arcs over a mountain, ringed in gold, with one star."""
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=NAVY, outline=GOLD,
              width=3)
    d.ellipse((cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6),
              outline=GOLD_L, width=1)
    # aurora arcs
    for i, col in enumerate(((127, 224, 168), (79, 195, 161), (190, 230, 200))):
        d.arc((cx - r + 8 + i * 4, cy - r + 2 + i * 7,
               cx + r - 8 - i * 4, cy + r - 14 - i * 3),
              start=195, end=345, fill=col, width=4)
    # mountain
    d.polygon([(cx - 20, cy + 16), (cx - 2, cy - 8), (cx + 6, cy + 4),
               (cx + 12, cy - 2), (cx + 24, cy + 16)], fill=(245, 239, 221))
    # star
    sx, sy, sr = cx + 13, cy - 16, 5
    d.polygon([(sx, sy - sr), (sx + 1.6, sy - 1.6), (sx + sr, sy),
               (sx + 1.6, sy + 1.6), (sx, sy + sr), (sx - 1.6, sy + 1.6),
               (sx - sr, sy), (sx - 1.6, sy - 1.6)],
              fill=(255, 214, 120))


# -------------------------------------------------------------- portrait
def draw_portrait():
    """Flat-illustration passport portrait: a woman of Auroria in a
    hand-knitted lopapeysa, braided hair, aurora sky behind her."""
    w, h = 148, 194
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # aurora sky gradient
    top = (14, 58, 74)
    bot = (31, 122, 92)
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c + (255,))
    # aurora bands
    for i, col in enumerate(((127, 224, 168, 110), (79, 195, 161, 90),
                             (190, 230, 200, 70))):
        d.arc((-30 - i * 8, 6 + i * 16, w + 30 + i * 8, 92 + i * 10),
              start=200, end=340, fill=col, width=9)
    # stars
    for (sx, sy) in ((18, 22), (128, 16), (112, 40), (30, 48), (138, 62),
                     (12, 78), (124, 84)):
        d.ellipse((sx - 1, sy - 1, sx + 1, sy + 1), fill=(255, 255, 255, 170))
    skin = (238, 195, 154)
    skin_d = (217, 160, 111)
    hair = (110, 79, 39)
    hair_d = (84, 58, 26)
    # shoulders / knitted sweater
    d.polygon([(4, h), (144, h), (140, 160), (110, 140), (97, 133),
               (51, 133), (38, 140), (8, 160)], fill=(243, 234, 218, 255))
    # yoke band with zig-zag
    d.polygon([(28, 156), (120, 156), (114, 172), (34, 172)],
              fill=(29, 58, 95, 255))
    for x0 in range(34, 114, 12):
        d.polygon([(x0, 172), (x0 + 6, 158), (x0 + 12, 172)],
                  fill=(176, 141, 60, 255))
    d.polygon([(28, 156), (120, 156), (116, 162), (32, 162)],
              fill=(176, 141, 60, 255))
    # collar
    d.polygon([(62, 134), (74, 146), (86, 134), (80, 132), (74, 140),
               (68, 132)], fill=(217, 200, 170, 255))
    # neck
    d.rectangle((65, 116, 83, 136), fill=skin_d + (255,))
    # braids behind shoulders
    for bx in (36, 100):
        d.rounded_rectangle((bx, 74, bx + 14, 168), radius=7,
                            fill=hair + (255,))
        for yy in range(80, 162, 12):
            d.line([(bx + 2, yy), (bx + 12, yy + 7)], fill=hair_d + (255,),
                   width=2)
        d.rectangle((bx - 1, 160, bx + 15, 167), fill=GOLD + (255,))
    # ears
    d.ellipse((42, 82, 49, 98), fill=skin + (255,))
    d.ellipse((99, 82, 106, 98), fill=skin + (255,))
    # face
    d.ellipse((46, 50, 102, 120), fill=skin + (255,))
    # hair cap + centre parting
    d.pieslice((40, 34, 108, 96), start=180, end=360, fill=hair + (255,))
    d.polygon([(70, 40), (78, 40), (74, 62)], fill=skin + (255,))
    d.arc((44, 40, 104, 92), start=180, end=360, fill=hair_d + (255,),
          width=2)
    # eyebrows
    d.line([(56, 84), (68, 82)], fill=(74, 52, 24, 255), width=2)
    d.line([(80, 82), (92, 84)], fill=(74, 52, 24, 255), width=2)
    # eyes
    for ex in (59, 83):
        d.ellipse((ex, 88, ex + 7, 94), fill=(42, 32, 24, 255))
        d.ellipse((ex + 2, 89, ex + 4, 91), fill=(255, 255, 255, 255))
    # nose
    d.line([(74, 94), (72, 104)], fill=(190, 140, 100, 255), width=2)
    d.line([(72, 104), (76, 105)], fill=(190, 140, 100, 255), width=2)
    # mouth: quiet closed smile
    d.arc((66, 106, 82, 118), start=15, end=165, fill=(163, 90, 74, 255),
          width=2)
    # blush
    for bx in (52, 86):
        d.ellipse((bx, 98, bx + 10, 106), fill=(214, 120, 90, 55))
    return img


# ---------------------------------------------------------------- stamps
def circular_stamp(color, city, country, date, kind, size=168):
    """Border-control round stamp, drawn straight (no curved text) so
    every word stays legible at small size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    d.ellipse((4, 4, size - 4, size - 4), outline=color + (255,), width=4)
    d.ellipse((16, 16, size - 16, size - 16), outline=color + (255,), width=2)
    fb = font(SANS_B, 16)
    fs = font(SANS_B, 13)
    centered(d, c, 44, city, fb, color + (255,))
    centered(d, c, 66, country, fs, color + (255,))
    d.line([(c - 52, 88), (c + 52, 88)], fill=color + (255,), width=2)
    centered(d, c, 94, date, fb, color + (255,))
    centered(d, c, 116, kind, fs, color + (255,), tracking=2)
    # stars flanking the kind
    for sx in (c - 58, c + 58):
        sy = 122
        d.polygon([(sx, sy - 4), (sx + 1.5, sy - 1.5), (sx + 4, sy),
                   (sx + 1.5, sy + 1.5), (sx, sy + 4), (sx - 1.5, sy + 1.5),
                   (sx - 4, sy), (sx - 1.5, sy - 1.5)], fill=color + (255,))
    return img


def rect_stamp(color, lines, w=218, h=118):
    """Rectangular border stamp: double rule, centred lines."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, w - 3, h - 3), outline=color + (255,), width=3)
    d.rectangle((9, 9, w - 9, h - 9), outline=color + (255,), width=1)
    fb = font(SANS_B, 16)
    fs = font(SANS_B, 13)
    n = len(lines)
    y = (h - (n * 24)) // 2 - 2
    for i, (txt, big) in enumerate(lines):
        centered(d, w // 2, y + i * 24, txt, fb if big else fs,
                 color + (255,))
    return img


def paste_rotated(page, stamp, cx, cy, angle):
    rot = stamp.rotate(angle, expand=True, resample=Image.BICUBIC)
    page.alpha_composite(rot, (int(cx - rot.width / 2),
                               int(cy - rot.height / 2)))


# -------------------------------------------------------------- left page
def draw_left_page(page, d):
    x0, y0, x1, y1 = 30, 46, 500, 978
    # frame
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=NAVY, width=2)
    d.rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), outline=GOLD, width=1)
    guilloche(page, x0 + 12, y0 + 12, x1 - 12, y1 - 12, NAVY)
    watermark(page, x0, y0, x1, y1, "AURORIA")

    # header: arms + titles
    coat_of_arms(d, 265, 106, 34)
    centered(d, 265, 152, "REPUBLIC OF AURORIA", font(SERIF_B, 25), NAVY,
             tracking=2)
    centered(d, 265, 182, "LÝÐVELDIÐ AURORIA", font(SERIF, 14), LABEL,
             tracking=3)
    centered(d, 265, 204, "PASSPORT  ·  VEGABRÉF", font(SERIF_B, 16), NAVY,
             tracking=1)
    d.line([(60, 232), (470, 232)], fill=NAVY, width=2)
    d.line([(60, 236), (470, 236)], fill=GOLD, width=1)
    # document number, top right
    d.text((392, 62), "AUR 847 291", font=font(MONO_B, 15), fill=NAVY)

    # portrait, top right of the data block
    px, py, pw, ph = 330, 256, 148, 194
    page.alpha_composite(draw_portrait(), (px, py))
    d.rectangle((px, py, px + pw, py + ph), outline=NAVY, width=2)
    d.rectangle((px + 4, py + 4, px + pw - 4, py + ph - 4), outline=GOLD,
                width=1)
    # gold office seal overlapping the portrait's lower-left corner
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    sx, sy, sr = 330, 446, 27
    od.ellipse((sx - sr, sy - sr, sx + sr, sy + sr),
               fill=(245, 239, 221, 235), outline=GOLD + (255,), width=3)
    od.ellipse((sx - sr + 6, sy - sr + 6, sx + sr - 6, sy + sr - 6),
               outline=GOLD + (255,), width=1)
    od.text((sx - 13, sy - 14), "★", font=font(SANS_B, 16),
            fill=GOLD + (255,))
    centered(od, sx, sy + 2, "SKARDVIK", font(SANS_B, 8), GOLD + (255,))
    page.alpha_composite(ov)

    # data fields, left column
    fields = [
        ("SURNAME / EFTIRNAFN", "HALLDÓRSDÓTTIR"),
        ("GIVEN NAMES / FORNÖFN", "SIGRÚN ELÍN"),
        ("NATIONALITY / ÞJÓÐERNI", "AURORIAN"),
        ("DATE OF BIRTH / FÆÐINGARDAGUR", "14 JUN 1994"),
        ("PLACE OF BIRTH / FÆÐINGARSTAÐUR", "SKARDVIK"),
        ("SEX / KYN", "F"),
        ("PERSONAL NO. / KENNITALA", "140694-3821"),
    ]
    y = 258
    for label, value in fields:
        d.text((48, y), label, font=font(SANS, 11), fill=LABEL)
        d.text((48, y + 14), value, font=font(SANS_B, 19), fill=INK)
        y += 46
    # height + eyes as two mini-columns (one line would overflow the column)
    d.text((48, y), "HEIGHT / HÆÐ", font=font(SANS, 11), fill=LABEL)
    d.text((48, y + 14), "172 cm", font=font(SANS_B, 19), fill=INK)
    d.text((180, y), "EYES / AUGU", font=font(SANS, 11), fill=LABEL)
    d.text((180, y + 14), "BLUE-GREY", font=font(SANS_B, 19), fill=INK)
    y += 46
    # issue block
    y += 6
    d.line([(48, y), (310, y)], fill=GOLD, width=1)
    y += 12
    for label, value in [
            ("DATE OF ISSUE / ÚTGÁFUDAGUR", ISSUE),
            ("DATE OF EXPIRY / GILDISTÍMI", EXPIRY),
            ("AUTHORITY / ÚTGEFANDI", "PASSPORT OFFICE, SKARDVIK")]:
        d.text((48, y), label, font=font(SANS, 11), fill=LABEL)
        d.text((48, y + 14), value, font=font(SANS_B, 19), fill=INK)
        y += 46
    # signature
    d.text((48, y + 2), "Sigrún Halldórsdóttir", font=font(SERIF_I, 21),
           fill=INK)
    d.line([(48, y + 32), (300, y + 32)], fill=INK, width=1)
    d.text((48, y + 38), "HOLDER'S SIGNATURE / UNDIRSKRIFT",
           font=font(SANS, 10), fill=LABEL)

    # machine-readable zone
    line1, line2 = build_mrz()
    d.rectangle((44, 884, 486, 962), fill=(255, 253, 245),
                outline=NAVY, width=1)
    d.text((58, 896), line1, font=font(MONO, 16), fill=INK)
    d.text((58, 924), line2, font=font(MONO, 16), fill=INK)


# ------------------------------------------------------------- right page
def draw_right_page(page, d):
    x0, y0, x1, y1 = 524, 46, 994, 978
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), outline=NAVY, width=2)
    d.rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), outline=GOLD, width=1)
    guilloche(page, x0 + 12, y0 + 12, x1 - 12, y1 - 12, NAVY)
    watermark(page, x0, y0, x1, y1, "AURORIA")

    centered(d, 759, 66, "VISAS", font(SERIF_B, 24), NAVY, tracking=4)
    centered(d, 759, 96, "ÁRITANIR", font(SERIF, 13), LABEL, tracking=3)
    d.text((946, 64), "12", font=font(SERIF_B, 16), fill=NAVY)
    d.line([(554, 126), (964, 126)], fill=NAVY, width=2)
    d.line([(554, 130), (964, 130)], fill=GOLD, width=1)

    # ---- Norwegian Schengen visa vignette
    vx0, vy0, vx1, vy1 = 548, 146, 970, 296
    d.rounded_rectangle((vx0, vy0, vx1, vy1), radius=8,
                        fill=(232, 238, 244), outline=NAVY, width=2)
    d.rounded_rectangle((vx0 + 5, vy0 + 5, vx1 - 5, vy1 - 5), radius=6,
                        outline=GOLD, width=1)
    d.text((566, 158), "KINGDOM OF NORWAY — VISA",
           font=font(SANS_B, 15), fill=NAVY)
    # mini Norwegian flag
    fx, fy = 906, 156
    d.rectangle((fx, fy, fx + 46, fy + 32), fill=(186, 12, 47),
                outline=NAVY, width=1)
    d.rectangle((fx + 14, fy, fx + 20, fy + 32), fill=(255, 255, 255))
    d.rectangle((fx, fy + 12, fx + 46, fy + 20), fill=(255, 255, 255))
    d.rectangle((fx + 16, fy, fx + 18, fy + 32), fill=(0, 32, 91))
    d.rectangle((fx, fy + 14, fx + 46, fy + 18), fill=(0, 32, 91))
    d.text((566, 186), "MULTIPLE ENTRY  ·  90 DAYS", font=font(SANS_B, 14),
           fill=INK)
    d.text((566, 210), "Valid:  01 JUN 2023 — 01 JUN 2024",
           font=font(SANS, 14), fill=INK)
    d.text((566, 232), "Issued:  OSLO, 18 MAY 2023",
           font=font(SANS, 14), fill=INK)
    d.text((566, 254), "No. NOR 552 118", font=font(MONO_B, 14), fill=INK)
    d.text((830, 254), "C  ·  NOR", font=font(SANS_B, 14), fill=NAVY)

    # ---- border stamps, chronological after the 12 MAR 2023 issue
    stamps = [
        ("circ", (46, 122, 47), "REYKJAVÍK", "ICELAND", "28 APR 2023",
         "ENTRY", -8, 640, 400),
        ("rect", NAVY, [("SKARDVIK", True), ("AURORIA — EXIT", False),
                        ("28 APR 2023", True)], 6, 856, 400),
        ("circ", (110, 60, 130), "TÓRSHAVN", "FAROE ISLANDS",
         "17 JUL 2023", "ENTRY", 5, 640, 560),
        ("rect", (140, 40, 40), [("BERGEN", True), ("NORWAY — ENTRY", False),
                                 ("02 SEP 2023", True)], -6, 856, 560),
        ("circ", (16, 110, 120), "NUUK", "GREENLAND", "21 JAN 2024",
         "ENTRY", 8, 640, 720),
        ("rect", NAVY, [("SKARDVIK", True), ("AURORIA — ARRIVAL", False),
                        ("30 JAN 2024", True)], -4, 856, 720),
    ]
    for kind, *rest in stamps:
        if kind == "circ":
            color, city, country, date, ek, ang, cx, cy = rest
            paste_rotated(page,
                          circular_stamp(color, city, country, date, ek),
                          cx, cy, ang)
        else:
            color, lines, ang, cx, cy = rest
            paste_rotated(page, rect_stamp(color, lines), cx, cy, ang)

    # ---- the telling detail: the Dark Months endorsement
    ex0, ey0, ex1, ey1 = 548, 872, 970, 962
    d.rectangle((ex0, ey0, ex1, ey1), outline=NAVY, width=2)
    d.rectangle((ex0 + 4, ey0 + 4, ex1 - 4, ey1 - 4), outline=GOLD, width=1)
    d.text((562, 882), "ENDORSEMENT  —  ATHUGASEMD",
           font=font(SANS_B, 12), fill=NAVY)
    note = ("Not valid for travel during the Dark Months (15 NOV – 15 JAN) "
            "except by ice-road permit issued at Skardvik. Holder is exempt "
            "from the Northern Lights levy (Art. 7).")
    yy = 902
    for ln in wrap(d, note, font(SANS, 13), ex1 - ex0 - 28):
        d.text((562, yy), ln, font=font(SANS, 13), fill=INK)
        yy += 17


# ------------------------------------------------------------------ main
def main():
    img = Image.new("RGBA", (W, H), DESK + (255,))
    d = ImageDraw.Draw(img)
    # desk shading: soft radial darkening toward the edges
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(40):
        a = int(26 * (1 - i / 40))
        od.rectangle((i, i, W - i, H - i), outline=(0, 0, 0, a))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    # spread shadow, then the two cream pages
    d.rounded_rectangle((36, 54, 1000, 986), radius=4, fill=(16, 20, 26))
    d.rectangle((30, 46, 500, 978), fill=CREAM)
    d.rectangle((524, 46, 994, 978), fill=CREAM)
    # spine
    d.rectangle((500, 46, 524, 978), fill=(214, 203, 175))
    d.line([(508, 46), (508, 978)], fill=(120, 105, 70), width=2)
    d.line([(516, 46), (516, 978)], fill=(120, 105, 70), width=1)
    draw_left_page(img, ImageDraw.Draw(img))
    draw_right_page(img, ImageDraw.Draw(img))
    img.convert("RGB").save(OUT, "PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}  {W}x{H}  {size} bytes")
    assert size <= 1_048_576, "over the 1 MiB gate"


if __name__ == "__main__":
    main()
