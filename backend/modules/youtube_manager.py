"""YouTube channel manager: upload, schedule, analytics.

Requires (one-time setup):
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
  - Google Cloud project with YouTube Data API v3 enabled
  - OAuth client_secret.json (Desktop type) placed in backend/
  - Scopes: youtube.upload, yt-analytics.readonly, youtube.readonly

Token is cached in backend/token.json after first browser approval.
Videos always upload as private unless publish_at/public is explicit.
"""

import os

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_LIBS = True
except Exception:
    GOOGLE_LIBS = False

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = os.environ.get("YT_CLIENT_SECRET_FILE", "client_secret.json")


def _service(api="youtube", version="v3"):
    if not GOOGLE_LIBS:
        raise RuntimeError("google-api libraries not installed")
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise RuntimeError(
                    f"{CLIENT_SECRET_FILE} missing — download OAuth client from Google Cloud"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build(api, version, credentials=creds)


def status():
    """Report whether channel management is ready."""
    return {
        "google_libs": GOOGLE_LIBS,
        "client_secret": os.path.exists(CLIENT_SECRET_FILE),
        "token": os.path.exists(TOKEN_FILE),
        "ready": GOOGLE_LIBS and os.path.exists(CLIENT_SECRET_FILE),
    }


def upload_video(video_path: str, title: str, description: str = "",
                 tags: list | None = None, privacy: str = "private",
                 publish_at: str | None = None):
    """Upload a video. privacy: private|unlisted|public. Default private."""
    yt = _service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": (tags or [])[:30],
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at  # RFC3339
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"upload progress: {int(status.progress() * 100)}%")
    return {"video_id": resp["id"], "url": f"https://youtu.be/{resp['id']}"}


def list_videos(max_results: int = 10):
    yt = _service()
    resp = yt.videos().list(
        part="snippet,statistics", myRating="none", maxResults=max_results
    ).execute()
    items = resp.get("items", [])
    # myRating filter needs channel id; simpler: uploads playlist
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()
    uploads_id = uploads["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    resp = yt.playlistItems().list(
        part="snippet", playlistId=uploads_id, maxResults=max_results
    ).execute()
    ids = [i["snippet"]["resourceId"]["videoId"] for i in resp.get("items", [])]
    if not ids:
        return []
    stats = yt.videos().list(part="snippet,statistics", id=",".join(ids)).execute()
    return [
        {
            "id": v["id"],
            "title": v["snippet"]["title"],
            "views": v["statistics"].get("viewCount", "0"),
            "likes": v["statistics"].get("likeCount", "0"),
        }
        for v in stats.get("items", [])
    ]


def channel_analytics(days: int = 28):
    yt = _service("youtubeAnalytics", "v2")
    end = "today"
    start = f"{days}daysAgo"
    resp = yt.reports().query(
        ids="channel==MINE",
        startDate=start,
        endDate=end,
        metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
    ).execute()
    return resp.get("rows", [])
