import requests
import os
from functools import lru_cache
from langchain_core.tools import tool
from duckduckgo_search import DDGS


@lru_cache(maxsize=128)
def _youtube_search_cached(query: str) -> list:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and len(api_key) > 10:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": api_key,
            "maxResults": 6,
            "type": "video",
            "regionCode": "IN"
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("items", []):
                snippet = item["snippet"]
                thumb = (
                    snippet.get("thumbnails", {}).get("high", {}).get("url")
                    or snippet.get("thumbnails", {}).get("medium", {}).get("url")
                )
                results.append({
                    "title": snippet["title"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "source": "YouTube",
                    "image_url": thumb,
                    "meta": snippet.get("channelTitle", "YouTube")
                })
            return results
        except Exception as e:
            print(f"YouTube API error: {e}")

    # Fallback DDG videos (broad search to ensure we get videos)
    try:
        ddgs = DDGS()
        res = []
        for item in ddgs.videos(query, max_results=6):
            res.append({
                "title": item.get("title", ""),
                "url": item.get("content", ""),
                "source": "Video Search",
                "image_url": item.get("images", {}).get("large") or item.get("images", {}).get("medium"),
                "meta": item.get("publisher", "Video")
            })
        if res:
            return res
    except Exception as e:
        print(f"YouTube fallback error: {e}")

    return [{"title": f"Search '{query}' on YouTube",
             "url": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
             "source": "YouTube", "image_url": None, "meta": "YouTube"}]


@tool
def youtube_search(query: str) -> list:
    """Search YouTube videos using Google API, returns thumbnails."""
    return _youtube_search_cached(query)


@lru_cache(maxsize=128)
def _youtube_music_search_cached(query: str) -> list:
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "music", "limit": 6}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            artist = item.get('artistName', '')
            track = item.get('trackName', '')
            full_title = f"{track} — {artist}"
            artwork = item.get("artworkUrl100", "").replace("100x100", "400x400")
            
            # Create a reliable YouTube Music search link
            import urllib.parse
            yt_query = urllib.parse.quote_plus(f"{track} {artist}")
            
            results.append({
                "title": full_title,
                "url": f"https://music.youtube.com/search?q={yt_query}",
                "source": "YouTube Music",
                "image_url": artwork or None,
                "meta": item.get("collectionName", "YouTube Music")
            })
        if results:
            return results
    except Exception as e:
        print(f"YT Music (iTunes) API error: {e}")

    return [{"title": f"Search '{query}' on YouTube Music",
             "url": f"https://music.youtube.com/search?q={query.replace(' ', '+')}",
             "source": "YouTube Music", "image_url": None, "meta": "YouTube Music"}]


@tool
def youtube_music_search(query: str) -> list:
    """Search music on YouTube Music."""
    return _youtube_music_search_cached(query)


@lru_cache(maxsize=128)
def _itunes_podcast_search_cached(query: str) -> list:
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "podcast", "limit": 6, "country": "IN"}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            artwork = item.get("artworkUrl600") or item.get("artworkUrl100")
            results.append({
                "title": item.get("trackName", ""),
                "url": item.get("trackViewUrl", ""),
                "source": "Apple Podcasts",
                "image_url": artwork or None,
                "meta": item.get("artistName", "Apple Podcasts")
            })
        return results
    except Exception as e:
        print(f"iTunes Podcast API error: {e}")
        return [{"title": f"Search '{query}' Podcasts",
                 "url": f"https://podcasts.apple.com/search?term={query.replace(' ', '+')}",
                 "source": "Apple Podcasts", "image_url": None, "meta": "Apple Podcasts"}]


@tool
def itunes_podcast_search(query: str) -> list:
    """Search podcasts on iTunes, returns artwork thumbnails."""
    return _itunes_podcast_search_cached(query)


@lru_cache(maxsize=128)
def _movie_search_cached(query: str) -> list:
    """Search for movies using multiple data sources."""
    import urllib.parse
    clean_query = query.strip().strip("'").strip('"')
    
    # Try iTunes first
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": f"{clean_query} movie", "limit": 1}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("resultCount", 0) > 0:
                item = data["results"][0]
                return [{
                    "title": item.get("trackName", clean_query),
                    "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_query)}+movie",
                    "source": "Movie Info",
                    "image_url": item.get("artworkUrl100", "").replace("100x100", "600x600"),
                    "meta": item.get("releaseDate", "Unknown")[:4]
                }]
    except: pass

    # Check YouTube for trailer/thumbnail
    try:
        results = youtube_search.invoke({"query": f"{clean_query} official trailer"})
        if results:
            trailer = results[0]
            return [{
                "title": f"{clean_query}",
                "url": trailer["url"],
                "source": "YouTube",
                "image_url": trailer["image_url"],
                "meta": "Trailer"
            }]
    except: pass

    # Last resort image search
    try:
        ddgs = DDGS()
        img_results = list(ddgs.images(f"{clean_query} movie poster", max_results=1))
        if img_results:
            return [{
                "title": clean_query,
                "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_query)}+movie",
                "source": "Web Movie",
                "image_url": img_results[0].get("image"),
                "meta": "Movie Recommendation"
            }]
    except: pass

    return [{"title": f"Explore '{clean_query}' on Web",
             "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_query)}+movie",
             "source": "Google", "image_url": None, "meta": "Search"}]


@tool
def tmdb_movie_search(query: str) -> list:
    """Search movies without TMDB restrictions."""
    return _movie_search_cached(query)


@lru_cache(maxsize=128)
def _google_news_search_cached(query: str) -> list:
    """Search news on Google News via RSS."""
    import urllib.parse
    import xml.etree.ElementTree as ET
    
    encoded_query = urllib.parse.quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        response = requests.get(rss_url, timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        results = []
        for item in root.findall(".//item")[:6]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            source_elem = item.find("source")
            pub_elem = item.find("pubDate")
            
            title = title_elem.text if title_elem is not None else "News Story"
            link = link_elem.text if link_elem is not None else ""
            source = source_elem.text if source_elem is not None else "Google News"
            pub_date = pub_elem.text if pub_elem is not None else ""
            
            results.append({
                "title": title,
                "url": link,
                "source": source,
                "image_url": None,
                "meta": pub_date.split(" +")[0] if pub_date else "Latest"
            })
        if results:
            return results
    except Exception as e:
        print(f"Google News RSS error: {e}")

    return [{"title": f"Search News: '{query}' on Google News",
             "url": f"https://news.google.com/search?q={encoded_query}",
             "source": "Google News", "image_url": None, "meta": "Google News"}]


@tool
def google_news_search(query: str) -> list:
    """Search news on Google News."""
    return _google_news_search_cached(query)
