#!/usr/bin/env python3
"""Burn captions into an mp4 without ffmpeg drawtext (this ffmpeg build lacks it): PIL renders each caption
to a PNG bar, ffmpeg overlays them with time windows.
  python3 tools/burn_captions.py in.mp4 captions.json out.mp4
captions.json: [{"start": 0.0, "end": 4.5, "text": "..."}, ...]   (text may contain \n)
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/SFNS.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    w, h = out.split(",")[:2]; return int(w), int(h)

def bar(text, w, h, tmp, i):
    f = font(max(22, h // 26)); pad = h // 40
    lines = text.split("\n")
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = max(d0.textbbox((0, 0), l, font=f)[2] for l in lines); lh = d0.textbbox((0, 0), "Ag", font=f)[3]
    bw, bh = tw + pad * 4, lh * len(lines) + pad * 2 + (len(lines) - 1) * (pad // 2)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x0, y0 = (w - bw) // 2, h - bh - h // 14
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=pad, fill=(0, 0, 0, 200))
    y = y0 + pad
    for l in lines:
        lw = d.textbbox((0, 0), l, font=f)[2]
        d.text(((w - lw) // 2, y), l, font=f, fill=(242, 242, 242, 255)); y += lh + pad // 2
    p = os.path.join(tmp, f"cap{i}.png"); img.save(p); return p

def main(src, caps_path, dst):
    caps = json.load(open(caps_path)); w, h = probe(src)
    with tempfile.TemporaryDirectory() as tmp:
        pngs = [bar(c["text"], w, h, tmp, i) for i, c in enumerate(caps)]
        cmd = ["ffmpeg", "-y", "-i", src]
        for p in pngs: cmd += ["-i", p]
        chain = []; prev = "[0:v]"
        for i, c in enumerate(caps):
            out = f"[v{i}]" if i < len(caps) - 1 else "[vout]"
            chain.append(f"{prev}[{i+1}:v]overlay=0:0:enable='between(t,{c['start']},{c['end']})'{out}"); prev = out
        cmd += ["-filter_complex", ";".join(chain), "-map", "[vout]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", dst]
        subprocess.run(cmd, check=True, capture_output=True)
    print("wrote", dst)

if __name__ == "__main__":
    main(*sys.argv[1:4])
