# Copyright (c) 2025 Riskyhater
# Licensed under the MIT License.
# This file is part of RoseXMusic


from pathlib import Path

from pyrogram import filters, types

from anony import anon, app, config, db, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await m.reply_text(m.lang["play_searching"])
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            try:
                await sent.delete()
            except Exception:
                pass
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            try:
                await sent.delete()
            except Exception:
                pass
            return

    if not file:
        try:
            await sent.delete()
        except Exception:
            pass
        return

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            await sent.edit_text(
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, m.lang["play_now"]
                ),
            )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        import os
        safe_id = str(file.id).replace(":", "_")
        for ext in (["mp4"] if video else ["webm", "m4a", "opus", "mp4"]):
            fname = f"downloads/{safe_id}.{ext}"
            if os.path.exists(fname):
                file.file_path = fname
                break
        if not file.file_path:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(
                file.id,
                video=video,
                fallback_url=getattr(file, "url", None),
                title=getattr(file, "title", None),
            )
        if not file.file_path:
            try:
                await sent.delete()
            except Exception:
                pass
            return

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )
