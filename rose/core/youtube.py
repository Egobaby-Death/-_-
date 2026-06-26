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
            for file in os.listdir(self.cookie_dir):
                if file.endswith(".txt"):
                    self.cookies.append(f"{self.cookie_dir}/{file}")
            self.checked = True
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("No YouTube cookies configured; using cookieless mode.")
            return None
        return random.choice(self.cookies)

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("Saving cookies from urls...")
        async with aiohttp.ClientSession() as session:
            for url in urls:
                name = url.split("/")[-1]
                link = "https://batbin.me/raw/" + name
                async with session.get(link) as resp:
                    resp.raise_for_status()
                    with open(f"{self.cookie_dir}/{name}.txt", "wb") as fw:
                        fw.write(await resp.read())
        logger.info(f"Cookies saved in {self.cookie_dir}.")

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            results = None

        if results and results.get("result"):
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )

        if not video:
            logger.info(f"YouTube search failed for '{query}', trying JioSaavn…")
            saavn = _get_saavn()
            track = await saavn.search(query, m_id)
            if track:
                logger.info(f"JioSaavn found: {track.title}")
                return track

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
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
        if video_id and video_id.startswith("jiosaavn:"):
            saavn = _get_saavn()
            return await saavn.download(fallback_url, video_id)

        url = self.base + video_id

        # Cache check
        for ext in (["mp4"] if video else ["webm", "m4a", "opus", "mp4"]):
            filename = f"downloads/{video_id}.{ext}"
            if Path(filename).exists():
                return filename

        cookie = self.get_cookies()
        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "noprogress": True,
            "noplaylist": True,
            "geo_bypass": True,
            "no_warnings": True,
            "overwrites": False,
            "nocheckcertificate": True,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 25,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "com.google.android.youtube/17.36.4 "
                    "(Linux; U; Android 12; GB) gzip"
                ),
            },
        }
        if cookie:
            base_opts["cookiefile"] = cookie

        if video:
            ydl_opts = {
                **base_opts,
                "format": (
                    "bestvideo[height<=?720][width<=?1280][ext=mp4]+bestaudio[ext=m4a]"
                    "/bestvideo[height<=?720]+bestaudio[ext=m4a]"
                    "/bestvideo+bestaudio"
                    "/best[ext=mp4]/best"
                ),
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": (
                    "bestaudio[ext=m4a]"
                    "/bestaudio[ext=webm]"
                    "/bestaudio"
                    "/best"
                ),
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError):
                    return None
                except Exception as ex:
                    logger.warning("YT download error: %s", ex)
                    return None
            return None

        await asyncio.to_thread(_download)

        # Post-download scan
        exts = ["mp4"] if video else ["webm", "m4a", "opus", "mp3", "mp4"]
        for ext in exts:
            filename = f"downloads/{video_id}.{ext}"
            if Path(filename).exists():
                return filename

        # YouTube failed — silently fallback to JioSaavn (audio only)
        if not video:
            query = title or video_id
            logger.info(f"YT download failed for '{query}', trying JioSaavn fallback…")
            saavn = _get_saavn()
            saavn_track = await saavn.search(query, 0)
            if saavn_track:
                result = await saavn.download(saavn_track.url, saavn_track.id)
                if result:
                    logger.info(f"JioSaavn fallback succeeded for '{query}'")
                    return result

        return None
