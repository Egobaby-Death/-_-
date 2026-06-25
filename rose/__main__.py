# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import asyncio
import signal
import importlib
import time          # ✅ ADDED (line 12)
import psutil        # ✅ ADDED (line 12)
from contextlib import suppress

# ✅ ADDED: boot, tasks to import (line 17)
from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt, boot, tasks)
from anony.plugins import all_modules

# ✅ ADDED: Ping interval in seconds (line 20)
PING_INTERVAL = 300

# ✅ ADDED: Auto ping function (lines 23–60)
async def auto_ping():
    """Automatic status ping every PING_INTERVAL seconds."""
    while True:
        try:
            # Memory usage
            mem = psutil.virtual_memory()
            ram_used = mem.used / 1024**3
            ram_total = mem.total / 1024**3
            cpu_percent = psutil.cpu_percent(interval=1)

            # Log or send ping (customize as needed)
            logger.info(f"🔁 Auto Ping | CPU: {cpu_percent}% | RAM: {ram_used:.1f}/{ram_total:.1f} GB")

            # Optional: Send to Telegram log channel if LOGGER_ID set
            if config.LOGGER_ID:
                await app.send_message(
                    config.LOGGER_ID,
                    f"✅ **Bot is alive**\n🖥 CPU: {cpu_percent}%\n💾 RAM: {ram_used:.1f}/{ram_total:.1f} GB"
                )

            # You can also add HTTP pings (e.g., to UptimeRobot) here
            # import aiohttp
            # async with aiohttp.ClientSession() as sess:
            #     await sess.get("https://your-ping-url.com")

        except Exception as e:
            logger.error(f"Auto ping failed: {e}")

        await asyncio.sleep(PING_INTERVAL)


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()


async def main():
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())
    logger.info(f"Loaded {len(app.sudoers)} sudo users.")

    # ✅ ADDED: Start auto-ping scheduler (lines 91–93)
    asyncio.create_task(auto_ping())

    await idle()
    asyncio.create_task(stop())


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
