#!/usr/bin/env python3
"""
Posts the next N unposted SHIVHOM reels to Instagram Reels and YouTube Shorts.

State is tracked in posted.json so re-runs never double-post.
Instagram requires a public video URL, so this script publishes from the
raw.githubusercontent.com URL of the file already committed to this repo
(the repo must be public, or use a private-repo-with-token raw URL).

Required env vars (set as GitHub Actions secrets):
  IG_USER_ID          - Instagram Business Account ID
  IG_ACCESS_TOKEN      - Long-lived Page/IG access token with instagram_content_publish
  GITHUB_REPOSITORY    - auto-set by Actions, e.g. "user/repo"
  GITHUB_SHA            - auto-set by Actions, commit the raw URL should point at
  YT_CLIENT_ID
  YT_CLIENT_SECRET
  YT_REFRESH_TOKEN
  FULL_SONG_URL         - link pinned/inserted into captions & descriptions
  REELS_PER_RUN          - optional, default 2
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REELS_JSON = os.path.join(ROOT, "reels.json")
POSTED_JSON = os.path.join(ROOT, "posted.json")
REELS_DIR = os.path.join(ROOT, "reels")

FULL_SONG_URL = os.environ.get("FULL_SONG_URL", "https://youtu.be/C97UVvWgAGM")
REELS_PER_RUN = int(os.environ.get("REELS_PER_RUN", "2"))


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def raw_video_url(reel_id):
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ.get("GITHUB_SHA", "main")
    fname = f"reel_{reel_id:02d}.mp4"
    return f"https://raw.githubusercontent.com/{repo}/{sha}/reels/{fname}"


def http_json(url, data=None, method="GET"):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


# ---------------- Instagram ----------------

def post_instagram(reel):
    ig_user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    caption = f"{reel['caption']}\n\n{reel['hashtags']}\n\n\U0001F3B5 Full song: {FULL_SONG_URL}"
    video_url = raw_video_url(reel["id"])

    create = http_json(
        f"https://graph.instagram.com/v21.0/{ig_user_id}/media",
        {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
        method="POST",
    )
    creation_id = create["id"]

    for _ in range(30):
        status = http_json(
            f"https://graph.instagram.com/v21.0/{creation_id}"
            f"?fields=status_code&access_token={token}"
        )
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"IG container failed: {status}")
        time.sleep(10)
    else:
        raise RuntimeError("IG container never finished processing")

    publish = http_json(
        f"https://graph.instagram.com/v21.0/{ig_user_id}/media_publish",
        {"creation_id": creation_id, "access_token": token},
        method="POST",
    )
    return publish["id"]


# ---------------- YouTube ----------------

def youtube_access_token():
    resp = http_json(
        "https://oauth2.googleapis.com/token",
        {
            "client_id": os.environ["YT_CLIENT_ID"],
            "client_secret": os.environ["YT_CLIENT_SECRET"],
            "refresh_token": os.environ["YT_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        method="POST",
    )
    return resp["access_token"]


def post_youtube(reel):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=youtube_access_token(),
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    youtube = build("youtube", "v3", credentials=creds)

    title = f"{reel['line1']} {reel['line2']} | SHIVHOM #Shorts"[:100]
    description = (
        f"{reel['caption']}\n\n{reel['hashtags']}\n\n"
        f"\U0001F3B5 Full song: {FULL_SONG_URL}\n#Shorts"
    )
    fname = os.path.join(REELS_DIR, f"reel_{reel['id']:02d}.mp4")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "10",  # Music
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(fname, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]


# ---------------- Queue ----------------

def main():
    reels = load_json(REELS_JSON, {}).get("reels", [])
    posted = load_json(POSTED_JSON, {})

    candidates = []
    for reel in reels:
        rid = reel["id"]
        fname = os.path.join(REELS_DIR, f"reel_{rid:02d}.mp4")
        entry = posted.get(str(rid), {})
        if os.path.exists(fname) and not (entry.get("instagram") and entry.get("youtube")):
            candidates.append(reel)
        if len(candidates) >= REELS_PER_RUN:
            break

    if not candidates:
        print("Nothing to post this run (queue empty or all reels posted).")
        return

    for reel in candidates:
        rid = str(reel["id"])
        entry = posted.setdefault(rid, {})
        print(f"Posting reel {rid} ...")

        if not entry.get("instagram"):
            try:
                media_id = post_instagram(reel)
                entry["instagram"] = True
                entry["instagram_media_id"] = media_id
                print(f"  Instagram OK: {media_id}")
            except Exception as e:
                print(f"  Instagram FAILED: {e}", file=sys.stderr)

        if not entry.get("youtube"):
            try:
                video_id = post_youtube(reel)
                entry["youtube"] = True
                entry["youtube_video_id"] = video_id
                print(f"  YouTube OK: {video_id}")
            except Exception as e:
                print(f"  YouTube FAILED: {e}", file=sys.stderr)

        entry["last_attempt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        save_json(POSTED_JSON, posted)

    save_json(POSTED_JSON, posted)


if __name__ == "__main__":
    main()
