"""
YouTube Data API v3 — Full, coherent smoke test
Retrieves (public) data:
- Channel details: snippet, statistics, contentDetails, brandingSettings, status, topicDetails
- Uploads playlist -> recent video IDs 
- Video details: snippet, statistics, contentDetails, status, topicDetails
- VideoCategories mapping (categoryId -> name)
- Sample top-level comments (with pagination option)
"""

import os
import time
import requests
from typing import Dict, List, Any, Optional

try:
    # Optional; if not installed, script still works via env var.
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Missing YOUTUBE_API_KEY. Set it as an environment variable or in a .env file.\n"
        "Example:\n  export YOUTUBE_API_KEY='YOUR_KEY'\n"
        "or create .env with:\n  YOUTUBE_API_KEY=YOUR_KEY"
    )

BASE_URL = "https://www.googleapis.com/youtube/v3"


def yt_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call YouTube Data API v3 with basic error handling."""
    params = dict(params)
    params["key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}"
    r = requests.get(url, params=params, timeout=30)

    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = r.text
        raise RuntimeError(f"API error {r.status_code} on {endpoint}: {err}")

    return r.json()


# Discovery (handle -> channelId)


def resolve_channel_id(query: str) -> str:
    """
    Resolve a channel using a handle or text query (e.g. '@veritasium').
    NOTE: Uses search.list (quota expensive). For production, store channel IDs and avoid this.
    """
    data = yt_get("search", {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 1,
    })
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"No channel found for query: {query}")
    return items[0]["snippet"]["channelId"]


# Channel

def get_channel_details_rich(channel_id: str) -> Dict[str, Any]:
    """
    Get channel details including optional enrichments.
    Parts:
    - snippet, contentDetails, statistics: core
    - brandingSettings, status, topicDetails: optional-but-useful enrichments
    """
    data = yt_get("channels", {
        "part": "snippet,contentDetails,statistics,brandingSettings,status,topicDetails",
        "id": channel_id
    })
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"No channel details returned for: {channel_id}")
    return items[0]


def list_upload_video_ids(uploads_playlist_id: str, max_videos: int = 25) -> List[str]:
    """
    Pull recent video IDs from the channel's uploads playlist (scalable).
    """
    video_ids: List[str] = []
    page_token: Optional[str] = None

    while len(video_ids) < max_videos:
        data = yt_get("playlistItems", {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": min(50, max_videos - len(video_ids)),
            "pageToken": page_token or ""
        })

        for it in data.get("items", []):
            vid = it.get("contentDetails", {}).get("videoId")
            if vid:
                video_ids.append(vid)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.1)

    return video_ids


# Videos

def get_videos_details_rich(video_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch video details in batches of 50.
    Parts:
    - snippet, statistics, contentDetails: core
    - status, topicDetails: enrichments + filtering signals
    """
    out: List[Dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        data = yt_get("videos", {
            "part": "snippet,statistics,contentDetails,status,topicDetails",
            "id": ",".join(batch),
            "maxResults": 50
        })
        out.extend(data.get("items", []))
        time.sleep(0.1)
    return out


# Video Categories (categoryId -> name)
def get_video_categories(region_code: str = "US") -> Dict[str, str]:
    """
    Map categoryId -> category title for a region.
    Useful for labeling/segmentation.
    """
    data = yt_get("videoCategories", {
        "part": "snippet",
        "regionCode": region_code
    })
    mapping: Dict[str, str] = {}
    for it in data.get("items", []):
        cid = it.get("id")
        title = it.get("snippet", {}).get("title")
        if cid and title:
            mapping[cid] = title
    return mapping


# Comments (top-level)

def get_top_level_comments(video_id: str, max_comments: int = 20, order: str = "relevance") -> List[Dict[str, Any]]:
    """
    Fetch top-level comments for a video (if comments enabled).
    order: 'relevance' or 'time'
    """
    comments: List[Dict[str, Any]] = []
    page_token: Optional[str] = None

    while len(comments) < max_comments:
        data = yt_get("commentThreads", {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(100, max_comments - len(comments)),
            "pageToken": page_token or "",
            "textFormat": "plainText",
            "order": order
        })

        for it in data.get("items", []):
            top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            comments.append({
                "author": top.get("authorDisplayName"),
                "publishedAt": top.get("publishedAt"),
                "likeCount": top.get("likeCount"),
                "text": top.get("textDisplay")
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.1)

    return comments


# Pretty printing helpers

def safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def print_channel_summary(channel: Dict[str, Any]) -> str:
    sn = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    uploads = safe_get(channel, ["contentDetails", "relatedPlaylists", "uploads"])

    print("\n2) Fetching channel details (rich)")
    print("   title:", sn.get("title"))
    print("   publishedAt:", sn.get("publishedAt"))
    print("   subscribers:", stats.get("subscriberCount"), "(may be hidden)")
    print("   totalViews:", stats.get("viewCount"))
    print("   videoCount:", stats.get("videoCount"))
    print("   uploads_playlist_id:", uploads)

    print("\n   == CHANNEL ENRICHMENTS ==")
    branding = channel.get("brandingSettings", {}).get("channel", {})
    print("   brandingSettings.channel.defaultLanguage:", branding.get("defaultLanguage"))
    print("   brandingSettings.channel.country:", branding.get("country"))
    print("   brandingSettings.channel.keywords:", branding.get("keywords"))
    print("   featuredChannelsUrls_count:", len(branding.get("featuredChannelsUrls", []) or []))

    status = channel.get("status", {})
    print("   status.privacyStatus:", status.get("privacyStatus"))
    print("   status.isLinked:", status.get("isLinked"))
    print("   status.longUploadsStatus:", status.get("longUploadsStatus"))
    print("   status.madeForKids:", status.get("madeForKids"))

    topic = channel.get("topicDetails", {})
    print("   topicDetails.topicCategories:", topic.get("topicCategories"))
    print("   topicDetails.topicIds:", topic.get("topicIds"))

    if not uploads:
        raise RuntimeError("Could not find uploads playlist id. Channel contentDetails missing.")

    return uploads


def print_video_summaries(videos: List[Dict[str, Any]], category_map: Dict[str, str]) -> None:
    print("\n4) Fetching video details + stats + duration + status + topicDetails")

    for v in videos[:5]:
        sn = v.get("snippet", {})
        st = v.get("statistics", {})
        cd = v.get("contentDetails", {})
        vs = v.get("status", {})
        td = v.get("topicDetails", {})

        cat_id = sn.get("categoryId")
        cat_name = category_map.get(cat_id, None) if cat_id else None

        print("\n   ---")
        print("   videoId:", v.get("id"))
        print("   title:", sn.get("title"))
        print("   publishedAt:", sn.get("publishedAt"))
        print("   channelTitle:", sn.get("channelTitle"))
        print("   categoryId:", cat_id, f"({cat_name})" if cat_name else "")
        print("   tags_count:", len(sn.get("tags", []) or []), "(tags may be missing)")
        print("   duration:", cd.get("duration"))  # ISO 8601 e.g. PT30M45S
        print("   caption_flag:", cd.get("caption"))
        print("   views:", st.get("viewCount"))
        print("   likes:", st.get("likeCount"), "(may be missing if disabled)")
        print("   comments:", st.get("commentCount"), "(may be missing)")
        print("   status.privacyStatus:", vs.get("privacyStatus"))
        print("   status.madeForKids:", vs.get("madeForKids"))
        print("   status.embeddable:", vs.get("embeddable"))
        print("   topicDetails.topicCategories:", td.get("topicCategories"))
        print("   topicDetails.topicIds:", td.get("topicIds"))


# Main

def main():
    # Change this to any handle or channel name to test discovery.
    # For production pipelines, do NOT use discovery repeatedly.
    HANDLE_OR_QUERY = "@veritasium"

    print(f"\n1) Resolving channel for handle/query: {HANDLE_OR_QUERY}")
    channel_id = resolve_channel_id(HANDLE_OR_QUERY)
    print("   channel_id:", channel_id)

    channel = get_channel_details_rich(channel_id)
    uploads_playlist_id = print_channel_summary(channel)

    print("\n3) Listing recent upload video IDs from uploads playlist")
    video_ids = list_upload_video_ids(uploads_playlist_id, max_videos=10)
    print("   got video_ids:", video_ids)

    print("\n3b) Fetching category mapping (US) for categoryId -> name")
    category_map = get_video_categories(region_code="US")
    print(f"   categories loaded: {len(category_map)}")

    videos = get_videos_details_rich(video_ids)
    print_video_summaries(videos, category_map)

    print("\n5) Fetching sample top-level comments for the first video (order=time)")
    first_video_id = videos[0]["id"] if videos else None
    if not first_video_id:
        print("   No videos returned — cannot fetch comments.")
        return

    try:
        comments = get_top_level_comments(first_video_id, max_comments=5, order="time")
        if not comments:
            print("   No comments returned (comments may be disabled or empty).")
        else:
            for c in comments:
                print("\n   ---")
                print("   author:", c.get("author"))
                print("   likeCount:", c.get("likeCount"))
                print("   publishedAt:", c.get("publishedAt"))
                text = c.get("text") or ""
                print("   text:", (text[:200] + "…") if len(text) > 200 else text)
    except RuntimeError as e:
        print("   Could not fetch comments:", e)

    print("\n✅ Full project-coverage smoke test complete.")


if __name__ == "__main__":
    main()
