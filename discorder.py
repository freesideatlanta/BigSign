import discord
import asyncio
from flask import url_for
from datetime import datetime
from typing import List, Dict, Any
from visher import Eventer

async def get_scheduled_events(tk):
    """
    Get all scheduled events from all Discord servers the bot has access to.
    
    Args:
        token: Discord bot token
        
    Returns:
        List of dictionaries containing event information
    """
    # Set up intents
    intents = discord.Intents.default()
    intents.guild_scheduled_events = True
    
    # Create client
    client = discord.Client(intents=intents)
    
    # Store events
    all_events = []
    
    @client.event
    async def on_ready():
        print(f'Logged in')
        print(f'Fetching events from {len(client.guilds)} servers...')
        guild = client.guilds[0]    
        try:
            events = await guild.fetch_scheduled_events()
            for event in events:
                # Create event info dictionary
                event_info = {
                    'id': event.id,
                    'name': event.name,
                    'description': event.description,
                    'start_time': event.start_time.isoformat() if event.start_time else None,
                    'end_time': event.end_time.isoformat() if event.end_time else None,
                    'status': str(event.status).split('.')[-1],  # scheduled, active, etc.
                    'interested_count': event.user_count,
                    'creator_id': event.creator.id if event.creator else None,
                    'creator_name': event.creator.name if event.creator else None,
                    'imageurl': event.cover_image,
                    'privacy_level': str(event.privacy_level).split('.')[-1] if hasattr(event, 'privacy_level') else None,
                }
                event_obj=Eventer(event_info,"Discord")
                all_events.append(event_obj)
        except discord.Forbidden:
            print(f"No permission to view events in {guild.name}")
        except Exception as e:
            print(f"Error fetching events from {guild.name}: {e}")
        
        # Close the client connection
        await client.close()
    
    # Run the client
    try:
        await client.start(tk)
    except discord.LoginFailure:
        print("Failed to login. Please check your token.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    await client.close()
    return all_events

    
    # Run the client

def discordEvents(tk):
    events = asyncio.run(get_scheduled_events(tk))
    return(events)
