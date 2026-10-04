import asyncio

import discord

from models import DiscordEvent
from visher import Eventer


async def get_scheduled_events(tk: str) -> list[Eventer]:
    """Get scheduled events from the bot's first Discord server."""
    intents = discord.Intents.default()
    intents.guild_scheduled_events = True
    client = discord.Client(intents=intents)
    all_events: list[Eventer] = []
    collection_error: Exception | None = None

    @client.event
    async def on_ready() -> None:
        nonlocal collection_error
        print("Logged in")
        try:
            if not client.guilds:
                return
            guild = client.guilds[0]
            events = await guild.fetch_scheduled_events()
            for event in events:
                payload = DiscordEvent(
                    id=event.id,
                    name=event.name,
                    start_time=event.start_time.isoformat(),
                    end_time=event.end_time.isoformat() if event.end_time else None,
                    interested_count=event.user_count,
                    imageurl=str(event.cover_image) if event.cover_image else None,
                )
                all_events.append(Eventer.from_discord(payload))
        except discord.Forbidden:
            print("No permission to view scheduled events")
        except Exception as error:
            # Discord dispatches callbacks in a task; propagate failure to the caller.
            collection_error = error
        finally:
            await client.close()

    try:
        await client.start(tk)
    except discord.LoginFailure:
        print("Failed to login. Please check your token.")
        return []
    finally:
        if not client.is_closed():
            await client.close()
    if collection_error is not None:
        raise collection_error
    return all_events


def discordEvents(tk: str) -> list[Eventer]:
    return asyncio.run(get_scheduled_events(tk))
