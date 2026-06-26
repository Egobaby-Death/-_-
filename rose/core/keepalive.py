import os
import asyncio
from aiohttp import web
from anony import logger


async def _health(request):
    return web.Response(text="🌹 Rose X Music — Bot is alive!", content_type="text/plain")


async def start_keepalive():
    port = int(os.getenv("PORT", 8080))
    server = web.Application()
    server.router.add_get("/", _health)
    server.router.add_get("/health", _health)
    server.router.add_get("/ping", _health)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Keep-alive server started on port {port}")
