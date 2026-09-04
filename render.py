#!/usr/bin/env python3
"""Render SHIVHOM reels: vertical 1080x1920, Ken Burns zoom, hook text overlay, audio slice."""
import json, os, subprocess, sys, math

BASE = "/home/user/work"
OUT  = os.path.join(BASE, "reels")
os.makedirs(OUT, exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
FPS = 30

def render(r, audio):
    dur = r["end"] - r["start"]
    n_frames = int(round(dur * FPS))
    img = os.path.join(BASE, "img", f"{r['img']}.jpg")
    out = os.path.join(OUT, f"reel_{r['id']:02d}.mp4")

    # hook text files (avoids drawtext escaping issues)
    l1 = os.path.join(BASE, "tmp_l1.txt")
    l2 = os.path.join(BASE, "tmp_l2.txt")
    with open(l1, "w") as f: f.write(r["line1"])
    with open(l2, "w") as f: f.write(r["line2"])

    # Ken Burns zoom
    rate = 0.16 / n_frames   # +-16% over the clip
    if r["zoom"] == "in":
        z = f"min(1.0+{rate:.8f}*on,1.30)"
    else:
        z = f"max(1.30-{rate:.8f}*on,1.0)"
    kb = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={n_frames}:s=1080x1920:fps={FPS},"
        f"format=yuv420p,"
        f"eq=saturation=1.08:contrast=1.04:brightness=0.0,"
        f"vignette=angle=PI/5,"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4:.3f}:d=0.4"
    )

    # hook text: pop in 3.6-5.6s
    def alpha_expr():
        return ("if(lt(t,3.6),0,if(lt(t,4.35),(t-3.6)/0.75,"
                "if(lt(t,5.0),1,if(lt(t,5.6),(5.6-t)/0.6,0))))")

    size1 = 96 if len(r["line1"]) <= 20 else 82
    size2 = 70 if len(r["line2"]) <= 20 else 62
    y1 = 0.560
    y2 = y1 + (size1 * 1.45) / 1920.0 + 0.012

    dt1 = (
        f"drawtext=fontfile={FONT_BOLD}:textfile={l1}:fontsize={size1}:"
        f"fontcolor=white:borderw=7:bordercolor=black@0.85:"
        f"shadowcolor=black@0.55:shadowx=0:shadowy=5:"
        f"x=(w-text_w)/2:y=h*{y1:.3f}:alpha='{alpha_expr()}'"
    )
    dt2 = (
        f"drawtext=fontfile={FONT_BOLD}:textfile={l2}:fontsize={size2}:"
        f"fontcolor=0xFFF3D0:borderw=6:bordercolor=black@0.85:"
        f"shadowcolor=black@0.55:shadowx=0:shadowy=4:"
        f"x=(w-text_w)/2:y=h*{y2:.3f}:alpha='{alpha_expr()}'"
    )

    vf = f"{kb},{dt1},{dt2}"

    af = (
        f"afade=t=in:st=0:d=0.4,afade=t=out:st={dur-0.45:.3f}:d=0.45,"
        f"loudnorm=I=-14:TP=-1.2:LRA=11"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", img,
        "-ss", f"{r['start']:.3f}", "-t", f"{dur:.3f}", "-i", audio,
        "-filter_complex",
        f"[0:v]{vf}[v];[1:a]{af}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-movflags", "+faststart",
        "-t", f"{dur:.3f}",
        out
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"REEL {r['id']}: FAILED\n{p.stderr[-800:]}")
        return False
    sz = os.path.getsize(out) / 1e6
    print(f"REEL {r['id']:02d}: OK  {dur:.1f}s  {sz:.1f}MB  {os.path.basename(out)}")
    return True

def main():
    with open(os.path.join(BASE, "reels.json")) as f:
        spec = json.load(f)
    audio = spec["audio"]
    only = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    ok = 0
    for r in spec["reels"]:
        if only and r["id"] not in only:
            continue
        if render(r, audio):
            ok += 1
    print(f"\nDONE: {ok} reels rendered -> {OUT}")

if __name__ == "__main__":
    main()
