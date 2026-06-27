import asyncio
import pyrogram

from anony import config, logger


_ANIM_FRAMES = [
    "ѕтαятιиg тнє вσт..",
    "ѕтαятιиg тнє вσт.....",
    "ѕтαятιиg тнє вσт..........",
    "ѕтαятιиg тнє вσт..........\n∂ιиg ∂σиg...",
    "ѕтαятιиg тнє вσт..........\n∂ιиg ∂σиg......",
    "ѕтαятιиg тнє вσт..........\n∂ιиg ∂σиg.........",
    "ѕтαятιиg тнє вσт..........\n∂ιиg ∂σиg.........\n\n<b>ѕтαятє∂</b> ✅",
]

_BOOT_STEPS = [
    "🌹 <b>Rose X Music</b> — Starting up...\n\n<blockquote>⟳ Connecting to Telegram...</blockquote>",
    "🌹 <b>Rose X Music</b> — Starting up...\n\n<blockquote>✅ Telegram connected\n⟳ Loading modules...</blockquote>",
    "🌹 <b>Rose X Music</b> — Starting up...\n\n<blockquote>✅ Telegram connected\n✅ Modules loaded\n⟳ Connecting to Database...</blockquote>",
    "🌹 <b>Rose X Music</b> — Starting up...\n\n<blockquote>✅ Telegram connected\n✅ Modules loaded\n✅ Database connected\n⟳ Starting voice engine...</blockquote>",
]

_BOOT_DONE = (
    "✅ <b>Rose X Music is Online!</b>\n\n"
    "<blockquote>"
    "🤖 Bot: {name}\n"
    "🆔 ID: <code>{bot_id}</code>\n"
    "🎙 Assistant: {assistant}\n"
    "📦 Version: 3.0.3"
    "</blockquote>"
)


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="anony",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        )
        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID
        self.bl_users = pyrogram.filters.user()
        self.sudoers = pyrogram.filters.user(self.owner)
        self._boot_msg = None

    async def boot(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            self._boot_msg = await self.send_message(self.logger, _ANIM_FRAMES[0])
            for frame in _ANIM_FRAMES[1:]:
                await asyncio.sleep(0.6)
                await self._boot_msg.edit_text(frame)

            await asyncio.sleep(1.0)

            await self._boot_msg.edit_text(_BOOT_STEPS[0])
            for step in _BOOT_STEPS[1:]:
                await asyncio.sleep(0.8)
                await self._boot_msg.edit_text(step)
        except Exception as ex:
            raise SystemExit(f"Bot has failed to access the log group: {self.logger}\nReason: {ex}")

        get = await self.get_chat_member(self.logger, self.id)
        if get.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR:
            raise SystemExit("Please promote the bot as an admin in logger group.")
        logger.info(f"Bot started as @{self.username}")

    async def finish_boot(self, assistant_name: str):
        if self._boot_msg:
            try:
                await self._boot_msg.edit_text(
                    _BOOT_DONE.format(
                        name=self.mention,
                        bot_id=self.id,
                        assistant=assistant_name or "N/A",
                    )
                )
            except Exception:
                pass

    async def exit(self):
        await super().stop()
        logger.info("Bot stopped.")
