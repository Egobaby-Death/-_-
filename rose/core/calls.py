import asyncio

from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
from pyrogram.errors import (ChatSendMediaForbidden, ChatSendPhotosForbidden,
                             MessageIdInvalid)
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from anony import (app, config, db, lang, logger,
                   queue, thumb, userbot, yt)
from anony.helpers import Media, Track, buttons


async def _send_play_log(chat_id: int, media, user_mention: str, chat_title: str) -> None:
    try:
        text = (
            f"🎵 <b>Now Playing</b>\n\n"
            f"<blockquote>"
            f"💬 Chat: <code>{chat_id}</code> | <b>{chat_title}</b>\n"
            f"👤 Requested by: {user_mention}\n"
            f"🎶 Title: <a href='{media.url}'>{media.title}</a>\n"
            f"⏱ Duration: {media.duration}\n"
            f"{'🎬 Video' if getattr(media, 'video', False) else '🎵 Audio'}"
            f"</blockquote>"
        )
        await app.send_message(chat_id=app.logger, text=text)
    except Exception as e:
        logger.error(f"Play log failed: {e}")


async def _send_stop_log(chat_id: int, reason: str, chat_title: str) -> None:
    try:
        text = (
            f"⏹️ <b>Playback {reason}</b>\n\n"
            f"<blockquote>"
            f"💬 Chat: <code>{chat_id}</code> | <b>{chat_title}</b>"
            f"</blockquote>"
        )
        await app.send_message(chat_id=app.logger, text=text)
    except Exception as e:
        logger.error(f"Stop log failed: {e}")


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)
        _thumb = (
            await thumb.generate(media)
            if isinstance(media, Track)
            else config.DEFAULT_THUMB
        ) if config.THUMB_GEN else None

        if not media.file_path:
            media.file_path = await yt.download(
                media.id,
                video=getattr(media, "video", False),
                fallback_url=getattr(media, "url", None),
                title=getattr(media, "title", None),
            )
        if not media.file_path:
            logger.warning(
                f"play_media: no file for '{getattr(media, 'title', media.id)}', skipping."
            )
            return await self.play_next(chat_id)

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
        )
        try:
            if not await db.get_call(chat_id):
                try:
                    await client.leave_call(chat_id, close=False)
                except Exception:
                    pass

            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=True),
            )
            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                try:
                    if _thumb:
                        await message.edit_media(
                            media=InputMediaPhoto(
                                media=_thumb,
                                caption=text,
                                has_spoiler=True,
                            ),
                            reply_markup=keyboard,
                        )
                    else:
                        await message.edit_text(text, reply_markup=keyboard)
                except (ChatSendMediaForbidden, ChatSendPhotosForbidden, MessageIdInvalid):
                    if _thumb:
                        sent = await app.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            reply_markup=keyboard,
                            has_spoiler=True,
                        )
                    else:
                        sent = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                        )
                    media.message_id = sent.id

                try:
                    chat = await app.get_chat(chat_id)
                    chat_title = chat.title or str(chat_id)
                except Exception:
                    chat_title = str(chat_id)
                asyncio.create_task(
                    _send_play_log(chat_id, media, media.user, chat_title)
                )

        except FileNotFoundError:
            logger.warning(
                f"play_media: file missing on disk for '{getattr(media, 'title', media.id)}', skipping."
            )
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_rtmp"])


    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def play_next(self, chat_id: int) -> None:
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        media = queue.get_next(chat_id)

        if not media:
            return await self.stop(chat_id)

        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except Exception:
            pass

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(
                media.id,
                video=media.video,
                fallback_url=getattr(media, "url", None),
                title=getattr(media, "title", None),
            )
            if not media.file_path:
                logger.warning(
                    f"Download failed for '{getattr(media, 'title', media.id)}', skipping."
                )
                return await self.play_next(chat_id)

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)


    async def ping(self) -> float:
        if not self.clients:
            return 0.0
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)


    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self.play_next(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)


    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
