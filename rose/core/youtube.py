# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils

_saavn = None

def _get_saavn():
    global _saavn
    if _saavn is None:
        from anony import saavn
        _saavn = saavn
    return _saavn

# Each strategy is tried in order before falling back to JioSaavn
_YT_STRATEGIES = [
    {
        "name": "android",
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "http_headers": {
            "User-Agent": (
                "com.google.android.youtube/17.36.4 "
                "(Linux; U; Android 12; GB) gzip"
            )
        },
    },
    {
        "name": "ios",
        "extractor_args": {"youtube": {"player_client": ["ios"]}},
        "http_headers": {
            "User-Agent": (
                "com.google.ios.youtube/19.29.1 "
                "(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)"
            )
        },
    },
    {
        "name": "tv_embed",
        "extractor_args": {"youtube": {"player_client": ["tv_embed", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.0) "
                "AppleWebKit/538.1 (KHTML, like Gecko) "
                "Version/6.0 TV Safari/538.1"
            )
        },
    },
    {
        "name": "mweb",
        "extractor_args": {"youtube": {"player_client": ["mweb", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Mobile Safari/537.36"
            )
        },
    },
]


def _scan_file(video_id: str, video: bool) -> str | None:
    exts = ["mp4"] if video else ["webm", "m4a", "opus", "mp3", "mp4"]
    # Minimum 100 KB — rejects corrupt/partial downloads that yt-dlp left behind
    min_size = 102_400
    for ext in exts:
        path = f"downloads/{video_id}.{ext}"
        if Path(path).exists() and Path(path).stat().st_size > min_size:
            return path
    return None


def _cleanup_partial(video_id: str) -> None:
    exts = ["webm", "m4a", "opus", "mp3", "mp4", "part", "ytdl"]
    for ext in exts:
        for pattern in [f"downloads/{video_id}.{ext}", f"downloads/{video_id}.{ext}.part"]:
            try:
                if Path(pattern).exists():
                    Path(pattern).unlink(missing_ok=True)
            except Exception:
                pass


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
        self.warned = False
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def get_cookies(self):
        if not self.checked:
            try:
                for file in os.listdir(self.cookie_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(f"{self.cookie_dir}/{file}")
            except Exception:
                pass
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("No YouTube cookies; running in cookieless mode.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    name = url.split("/")[-1]
                    link = "https://batbin.me/raw/" + name
                    async with session.get(link) as resp:
                        resp.raise_for_status()
                        with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                            fw.write(await resp.read())
            logger.info(f"Cookies saved in {self.cookie_dir}.")
        except Exception as e:
            logger.warning(f"Cookie save error: {e}")

    def valid(self, url: str) -> bool:
        try:
            return bool(re.match(self.regex, url))
        except Exception:
            return False

    def invalid(self, url: str) -> bool:
        try:
            return bool(re.match(self.iregex, url))
        except Exception:
            return False

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            results = None

        if results and results.get("result"):
            try:
                data = results["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name=(data.get("channel") or {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=(data.get("title") or "Unknown")[:25],
                    thumbnail=(
                        (data.get("thumbnails") or [{}])[-1]
                        .get("url", "")
                        .split("?")[0]
                    ),
                    url=data.get("link"),
                    view_count=(data.get("viewCount") or {}).get("short"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"YouTube search parse error: {e}")

        if not video:
            try:
                logger.info(f"YouTube search failed for '{query}', trying JioSaavn…")
                saavn = _get_saavn()
                track = await saavn.search(query, m_id)
                if track:
                    logger.info(f"JioSaavn found: {track.title}")
                    return track
            except Exception as e:
                logger.warning(f"JioSaavn search fallback error: {e}")

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                try:
                    track = Track(
                        id=data.get("id"),
                        channel_name=(data.get("channel") or {}).get("name", ""),
                        duration=data.get("duration"),
                        duration_sec=utils.to_seconds(data.get("duration")),
                        title=(data.get("title") or "Unknown")[:25],
                        thumbnail=(
                            (data.get("thumbnails") or [{}])[-1]
                            .get("url", "")
                            .split("?")[0]
                        ),
                        url=(data.get("link") or "").split("&list=")[0],
                        user=user,
                        view_count="",
                        video=video,
                    )
                    tracks.append(track)
                except Exception:
                    pass
        except Exception:
            pass
        return tracks

    async def download(
        self,
        video_id: str,
        video: bool = False,
        fallback_url: str = None,
        title: str = None,
    ) -> str | None:
        try:
            # JioSaavn direct download
            if video_id and video_id.startswith("jiosaavn:"):
                try:
                    saavn = _get_saavn()
                    return await saavn.download(fallback_url, video_id)
                except Exception as e:
                    logger.warning(f"JioSaavn direct download error: {e}")
                    return None

            url = self.base + video_id

            # Cache check (only return if file is non-empty)
            cached = _scan_file(video_id, video)
            if cached:
                return cached

            cookie = self.get_cookies()

            base_opts = {
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "noprogress": True,
                "noplaylist": True,
                "geo_bypass": True,
                "no_warnings": True,
                "overwrites": True,
                "nocheckcertificate": True,
                "retries": 2,
                "fragment_retries": 2,
                "socket_timeout": 20,
            }
            if cookie:
                base_opts["cookiefile"] = cookie

            if video:
                fmt = (
                    "bestvideo[height<=?720][width<=?1280][ext=mp4]+bestaudio[ext=m4a]"
                    "/bestvideo[height<=?720]+bestaudio[ext=m4a]"
                    "/bestvideo+bestaudio/best[ext=mp4]/best"
                )
                extra = {"format": fmt, "merge_output_format": "mp4"}
            else:
                fmt = (
                    "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"
                )
                extra = {"format": fmt}

            # Try each strategy in order (android first — best without cookies)
            for strategy in _YT_STRATEGIES:
                ydl_opts = {
                    **base_opts,
                    **extra,
                    "extractor_args": strategy["extractor_args"],
                    "http_headers": strategy["http_headers"],
                }

                def _do_download(opts=ydl_opts):
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        try:
                            ydl.download([url])
                        except Exception:
                            pass

                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(_do_download),
                        timeout=45,
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"YT strategy '{strategy['name']}' timed out for {video_id}")
                except Exception as e:
                    logger.warning(f"YT strategy '{strategy['name']}' error: {e}")

                result = _scan_file(video_id, video)
                if result:
                    logger.info(f"YT download ok via '{strategy['name']}': {video_id}")
                    return result

                # Clean up partial files before next strategy
                _cleanup_partial(video_id)
                logger.warning(f"YT strategy '{strategy['name']}' failed for {video_id}")

                # After first YT strategy fails (audio only) — immediately try JioSaavn
                # This avoids waiting 3 more slow strategies when YT is fully blocked
                if not video and strategy["name"] == "android":
                    query = title or video_id
                    logger.info(f"android failed, quick-trying JioSaavn for '{query}'…")
                    try:
                        saavn = _get_saavn()
                        saavn_track = await saavn.search(query, 0)
                        if saavn_track:
                            result = await saavn.download(saavn_track.url, saavn_track.id)
                            if result:
                                logger.info(f"JioSaavn quick fallback succeeded for '{query}'")
                                return result
                    except Exception as e:
                        logger.warning(f"JioSaavn quick fallback error: {e}")

            # All YouTube strategies failed — JioSaavn fallback (audio only)
            if not video:
                query = title or video_id
                logger.info(f"All YT strategies failed for '{query}', trying JioSaavn…")
                try:
                    saavn = _get_saavn()
                    saavn_track = await saavn.search(query, 0)
                    if saavn_track:
                        result = await saavn.download(saavn_track.url, saavn_track.id)
                        if result:
                            logger.info(f"JioSaavn fallback succeeded for '{query}'")
                            return result
                except Exception as e:
                    logger.warning(f"JioSaavn fallback error: {e}")

            return None

        except Exception as e:
            logger.warning(f"download() unexpected error: {e}")
            return None
