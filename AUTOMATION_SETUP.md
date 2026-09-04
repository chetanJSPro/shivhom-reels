# SHIVHOM reel automation — setup

This repo now auto-posts one reel at **7:30 AM IST** and one at **8:00 PM IST**
(the two peak windows from the playbook) via `.github/workflows/post-reels.yml`,
until all reels in `reels.json` are posted. State lives in `posted.json` so it
never double-posts or skips a reel.

You need to do the one-time setup below before it can actually publish anything.
Nothing here can be done on your behalf — both platforms require you to prove
you own the accounts.

## 1. Push this repo to GitHub

The workflow needs to live in a GitHub repo (public, since Instagram's API
needs a public URL to fetch each video from — it'll use
`raw.githubusercontent.com/<you>/<repo>/<sha>/reels/reel_XX.mp4`).

```
gh repo create shivhom-reels --public --source=. --push
```

(or create it on github.com and `git remote add origin ... && git push -u origin master`)

## 2. Instagram — Graph API access

1. Make sure your Instagram account is a **Business or Creator account**,
   linked to a **Facebook Page** you manage.
2. Go to [developers.facebook.com](https://developers.facebook.com) → create an app
   (type: "Business").
3. Add the **Instagram Graph API** product.
4. Under App Roles, add yourself as an Admin/Developer (needed while the app
   is in Development mode — up to 25 testers, no Meta review required as long
   as only you're posting to your own account).
5. Use the Graph API Explorer (or a short OAuth script) to get a **User
   Access Token** with scopes: `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`, `pages_read_engagement`.
6. Exchange it for a **long-lived token** (60 days):
   `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token=SHORT_TOKEN`
7. Get your **Instagram Business Account ID**:
   `GET /me/accounts` → find your Page → `GET /{page-id}?fields=instagram_business_account`
8. You'll need to refresh the long-lived token every ~60 days (or set up a
   scheduled refresh — ask me later and I'll add a workflow step for it).

**GitHub secrets to add** (repo Settings → Secrets and variables → Actions):
- `IG_USER_ID` — the Instagram Business Account ID from step 7
- `IG_ACCESS_TOKEN` — the long-lived token from step 6

## 3. YouTube — Data API v3 access

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create
   a project.
2. Enable the **YouTube Data API v3**.
3. Configure the OAuth consent screen (External, add yourself as a test user —
   no Google review needed while in Testing mode).
4. Create OAuth **client credentials** (type: Desktop app). Note the
   client ID and client secret.
5. Run a one-time local script (I can write this for you) to complete the
   OAuth flow in your browser and capture a **refresh token** with scope
   `https://www.googleapis.com/auth/youtube.upload`. This only needs to be
   done once — the refresh token doesn't expire unless revoked.

**GitHub secrets to add:**
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

## 4. Optional repo variable

- `FULL_SONG_URL` (Settings → Secrets and variables → Actions → Variables) —
  defaults to `https://youtu.be/C97UVvWgAGM` if unset.

## 5. Test it

Once secrets are set, go to **Actions → Post SHIVHOM reels → Run workflow**
to trigger a manual post and confirm both platforms work before trusting the
cron schedule.

## Notes

- Only 10 of the 19 planned reels (`reel_01.mp4`–`reel_10.mp4`) exist in
  `reels/` right now — the script only posts reels whose file actually
  exists, so it'll naturally pause once it runs out until reels 11–19 are
  added.
- Cron times are in UTC in the workflow file (`02:00` and `14:30` UTC =
  `7:30 AM` / `8:00 PM` IST). GitHub Actions cron can run a few minutes late
  under load — that's normal and doesn't meaningfully affect reach.
- Tokens are secrets, not files — never commit them to the repo.
