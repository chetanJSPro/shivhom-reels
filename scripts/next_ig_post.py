#!/usr/bin/env python3
"""
Shows the next Instagram reel to post, ready to copy-paste, and marks it
posted once you confirm. No API, no automation risk - just makes the
manual 2x/day posting fast.

Usage:
    python scripts/next_ig_post.py            # show next reel to post
    python scripts/next_ig_post.py --posted   # mark it posted, show the one after
"""
import json
import os
import subprocess
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REELS_JSON = os.path.join(ROOT, "reels.json")
POSTED_JSON = os.path.join(ROOT, "ig_posted.json")
REELS_DIR = os.path.join(ROOT, "reels")
FULL_SONG_URL = "https://youtu.be/C97UVvWgAGM"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    reels = load_json(REELS_JSON, {}).get("reels", [])
    posted = load_json(POSTED_JSON, {"done": []})

    if "--posted" in sys.argv and posted["done"]:
        print(f"Marked reel {posted['done'][-1]} as posted.")

    next_reel = None
    for reel in reels:
        rid = reel["id"]
        fname = os.path.join(REELS_DIR, f"reel_{rid:02d}.mp4")
        if os.path.exists(fname) and rid not in posted["done"]:
            next_reel = reel
            break

    if not next_reel:
        print("Nothing left to post (or files not generated yet).")
        return

    rid = next_reel["id"]
    fname = os.path.join(REELS_DIR, f"reel_{rid:02d}.mp4")
    caption = f"{next_reel['caption']}\n\n{next_reel['hashtags']}\n\n🎵 Full song: {FULL_SONG_URL}"

    print("=" * 50)
    print(f"NEXT REEL TO POST: reel_{rid:02d}.mp4")
    print("=" * 50)
    print(f"\nFile: {fname}\n")
    print("Caption (copy everything below):\n")
    print(caption)
    print("\n" + "=" * 50)
    print("After you've posted it, run:")
    print("  python scripts/next_ig_post.py --posted")
    print("=" * 50)

    if "--posted" in sys.argv:
        posted["done"].append(rid)
        save_json(POSTED_JSON, posted)
    else:
        # opens the file's folder so you can grab it fast
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", fname])
        except Exception:
            pass


if __name__ == "__main__":
    main()
