import asyncio
import signal
import importlib
import psutil
import time
from pathlib import Path
from contextlib import suppress

from anony import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt, boot, tasks)
from anony.plugins import all_modules
from anony.core.keepalive import start_keepalive

PING_INTERVAL = 300


async def auto_ping():
    while True:
        try:
            mem = psutil.virtual_memory()
            ram_used = mem.used / 1024**3
            ram_total = mem.total / 1024**3
            cpu_percent = psutil.cpu_percent(interval=1)
            assistants = len(userbot.clients)
            msg = (
                f"🔁 <b>Auto Ping</b>\n"
                f"├ CPU: <code>{cpu_percent}%</code>\n"
                f"├ RAM: <code>{ram_used:.1f}/{ram_total:.1f} GB</code>\n"
                f"└ Assistants: <code>{assistants}</code>"
            )
            logger.info(f"Auto Ping | CPU: {cpu_percent}% | RAM: {ram_used:.1f}/{ram_total:.1f} GB | Assistants: {assistants}")
            try:
                await app.send_message(config.LOGGER_ID, msg)
            except Exception as e:
                logger.warning(f"Auto ping to LOGGER_ID failed: {e}")
        except Exception as e:
            logger.error(f"Auto ping failed: {e}")
        await asyncio.sleep(PING_INTERVAL)


async def auto_cleanup():
    """Delete downloaded files older than 2 hours to keep Railway disk free."""
    downloads = Path("downloads")
    downloads.mkdir(exist_ok=True)
    while True:
        await asyncio.sleep(3600)
        try:
            now = time.time()
            deleted = 0
            for f in downloads.iterdir():
                if f.is_file() and (now - f.stat().st_mtime) > 7200:
                    f.unlink(missing_ok=True)
                    deleted += 1
            if deleted:
                logger.info(f"🧹 Auto-cleanup: removed {deleted} old file(s) from downloads/")
        except Exception as e:
            logger.error(f"Auto-cleanup failed: {e}")


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

    asyncio.create_task(auto_ping())
    asyncio.create_task(start_keepalive())
    asyncio.create_task(auto_cleanup())

    await idle()
    asyncio.create_task(stop())


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        pass
