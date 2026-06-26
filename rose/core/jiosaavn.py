# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import asyncio
import aiohttp
from pathlib import Path

from anony import logger
from anony.helpers import Track

RAPIDAPI_HOST = "jiosaavn-api-privatecvc2.p.rapidapi.com"
SEARCH_URL = f"https://{RAPIDAPI_HOST}/search/songs"


class JioSaavn:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": api_key,
        }
        self.enabled = bool(api_key)

    async def search(self, query: str, m_id: int) -> "Track | None":
        if not self.enabled:
            return None
        try:
            params = {"query": query, "page": "1", "limit": "1"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    SEARCH_URL,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"JioSaavn search HTTP {resp.status}")
                        return None
                    data = await resp.json(content_type=None)

            results = (data.get("data") or {}).get("results", [])
            if not results:
                return None

            song = results[0]
            song_id = song.get("id", "unknown")

            download_url = None
            for entry in reversed(song.get("downloadUrl") or []):
                if entry.get("url"):
                    download_url = entry["url"]
                    break

            if not download_url:
                return None

            duration_sec = int(song.get("duration") or 0)
            mins, secs = divmod(duration_sec, 60)
            duration = f"{mins:02d}:{secs:02d}"

            title = (song.get("name") or "Unknown")[:25]
            thumbnail = ((song.get("image") or [{}])[-1] or {}).get("url", "")
            primaries = (song.get("artists") or {}).get("primary", [])
            artist = primaries[0].get("name", "JioSaavn") if primaries else "JioSaavn"

            return Track(
                id=f"jiosaavn:{song_id}",
                channel_name=artist,
                duration=duration,
                duration_sec=duration_sec,
                message_id=m_id,
                title=title,
                thumbnail=thumbnail,
                url=download_url,
                view_count=None,
                video=False,
            )
        except asyncio.TimeoutError:
            logger.warning("JioSaavn search timed out")
            return None
        except Exception as e:
            logger.warning(f"JioSaavn search error: {e}")
            return None

    async def download(self, song_url: str, song_id: str) -> "str | None":
        if not song_url:
            return None

        try:
            safe_id = str(song_id).replace("jiosaavn:", "")
            filename = f"downloads/js_{safe_id}.m4a"

            if Path(filename).exists() and Path(filename).stat().st_size > 1024:
                return filename

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    song_url,
                    timeout=aiohttp.ClientTimeout(total=90),
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"JioSaavn download HTTP {resp.status}")
                        return None
                    with open(filename, "wb") as f:
                        async for chunk in resp.content.iter_chunked(16384):
                            if chunk:
                                f.write(chunk)

            if Path(filename).exists() and Path(filename).stat().st_size > 1024:
                return filename
            Path(filename).unlink(missing_ok=True)
            return None

        except asyncio.TimeoutError:
            logger.warning(f"JioSaavn download timed out: {song_id}")
            try:
                Path(f"downloads/js_{str(song_id).replace('jiosaavn:','')}.m4a").unlink(missing_ok=True)
            except Exception:
                pass
            return None
        except Exception as e:
            logger.warning(f"JioSaavn download error: {e}")
            try:
                Path(f"downloads/js_{str(song_id).replace('jiosaavn:','')}.m4a").unlink(missing_ok=True)
            except Exception:
                pass
            return None
