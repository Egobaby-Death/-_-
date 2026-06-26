# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot
#
# JioSaavn integration using public API (no RapidAPI key required).
# Search  → https://www.jiosaavn.com/api.php  (official web endpoint)
# Download → yt-dlp JioSaavn extractor (built-in, no key needed)

import asyncio
import urllib.parse
import aiohttp
import yt_dlp
from pathlib import Path

from anony import logger
from anony.helpers import Track

_SEARCH_URL = (
    "https://www.jiosaavn.com/api.php"
    "?__call=search.getResults"
    "&_format=json"
    "&_marker=0"
    "&api_version=4"
    "&ctx=web6dot0"
    "&n=1"
    "&q={query}"
)


class JioSaavn:
    def __init__(self, api_key: str = ""):
        # api_key is kept for backwards compatibility but is no longer required
        self.api_key = api_key
        self.enabled = True

    async def search(self, query: str, m_id: int) -> "Track | None":
        try:
            url = _SEARCH_URL.format(query=urllib.parse.quote(query))
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            f"JioSaavn search HTTP {resp.status} for '{query}'"
                        )
                        return None
                    data = await resp.json(content_type=None)

            results = data.get("results", [])
            if not results:
                logger.warning(f"JioSaavn: no results for '{query}'")
                return None

            song = results[0]
            mi = song.get("more_info") or {}

            song_id = song.get("id", "unknown")
            perma_url = song.get("perma_url", "")
            if not perma_url:
                return None

            duration_sec = int(mi.get("duration") or 0)
            mins, secs = divmod(duration_sec, 60)
            duration = f"{mins:02d}:{secs:02d}"

            title = (song.get("title") or "Unknown")[:25]
            image = song.get("image") or ""
            # use high-res thumbnail
            thumbnail = image.replace("-150x150.jpg", "-500x500.jpg")

            artist_map = (mi.get("artistMap") or {})
            primaries = artist_map.get("primary_artists", [])
            if isinstance(primaries, list) and primaries:
                artist = primaries[0].get("name", "JioSaavn")
            else:
                artist = "JioSaavn"

            return Track(
                id=f"jiosaavn:{song_id}",
                channel_name=artist,
                duration=duration,
                duration_sec=duration_sec,
                message_id=m_id,
                title=title,
                thumbnail=thumbnail,
                url=perma_url,
                view_count=None,
                video=False,
            )

        except asyncio.TimeoutError:
            logger.warning(f"JioSaavn search timed out for '{query}'")
            return None
        except Exception as e:
            logger.warning(f"JioSaavn search error: {e}")
            return None

    async def download(self, song_url: str, song_id: str) -> "str | None":
        if not song_url:
            return None

        try:
            safe_id = str(song_id).replace("jiosaavn:", "")
            filename_base = f"downloads/js_{safe_id}"

            for ext in ("m4a", "mp4", "webm"):
                p = Path(f"{filename_base}.{ext}")
                if p.exists() and p.stat().st_size > 1024:
                    return str(p)

            ydl_opts = {
                "outtmpl": f"{filename_base}.%(ext)s",
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "quiet": True,
                "noprogress": True,
                "noplaylist": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "retries": 3,
                "socket_timeout": 20,
            }

            def _do_download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([song_url])

            await asyncio.wait_for(
                asyncio.to_thread(_do_download),
                timeout=90,
            )

            for ext in ("m4a", "mp4", "webm", "opus"):
                p = Path(f"{filename_base}.{ext}")
                if p.exists() and p.stat().st_size > 1024:
                    logger.info(f"JioSaavn download ok: {p}")
                    return str(p)

            logger.warning(f"JioSaavn download: no output file for {song_id}")
            return None

        except asyncio.TimeoutError:
            logger.warning(f"JioSaavn download timed out: {song_id}")
            return None
        except Exception as e:
            logger.warning(f"JioSaavn download error: {e}")
            return None
