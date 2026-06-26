from pyrogram import Client

from anony import config, logger


class Userbot(Client):
    def __init__(self):
        self.clients = []
        clients = {"one": "SESSION1", "two": "SESSION2", "three": "SESSION3"}
        for key, string_key in clients.items():
            name = f"AnonyUB{key[-1]}"
            session = getattr(config, string_key)
            setattr(
                self,
                key,
                Client(
                    name=name,
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session,
                ),
            )

    async def boot_client(self, num: int):
        clients = {1: self.one, 2: self.two, 3: self.three}
        client = clients[num]
        try:
            await client.start()

            client.id = client.me.id
            client.name = client.me.first_name
            client.username = client.me.username
            client.mention = client.me.mention
            self.clients.append(client)
            logger.info(f"Assistant {num} started as @{client.username}")

            try:
                await client.send_message(config.LOGGER_ID, f"✅ Assistant {num} (@{client.username}) started.")
            except Exception as e:
                logger.warning(f"Assistant {num} couldn't message logger group: {e}")

        except Exception as e:
            logger.error(f"Assistant {num} failed to start: {e}")

    async def boot(self):
        if config.SESSION1:
            await self.boot_client(1)
        if config.SESSION2:
            await self.boot_client(2)
        if config.SESSION3:
            await self.boot_client(3)

        if not self.clients:
            logger.error(
                "No assistants started! Check SESSION env var and ensure the "
                "session string is valid."
            )

        from anony import app
        assistant_names = ", ".join(
            f"@{c.username}" for c in self.clients if hasattr(c, "username") and c.username
        )
        await app.finish_boot(assistant_names or "None — check SESSION")

    async def exit(self):
        for key in ("one", "two", "three"):
            client = getattr(self, key, None)
            if client and hasattr(client, "is_connected") and client.is_connected:
                try:
                    await client.stop()
                except Exception:
                    pass
        logger.info("Assistants stopped.")
