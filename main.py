# 9/26 (migrated handlers to MyClient below)

# 10/3

import discord

from discord import app_commands

GUILD_ID = 1418496208543940659
MY_GUILD = discord.Object(id=GUILD_ID)
MY_GUILD = discord.Object(id=GUILD_ID)

# Consolidated bot script
# - single client (MyClient)
# - message-based keyword replies (on_message)
# - slash command `spam` with range-limited `count`
# - a sample command `ping` that sends a button (command-based, not slash)
# - diagnostics for guild sync and fallback to global sync

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import sys
import asyncio
import os
from keep_alive import keep_alive

# --- Configuration ---
GUILD_ID = 1418496208543940659  # replace with your target guild ID
MY_GUILD = discord.Object(id=GUILD_ID)
TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("Please set DISCORD_TOKEN or TOKEN environment variable")

# --- Client class ---
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Copy global commands to guild for faster testing, but fall back to global sync if not possible.
        self.tree.copy_global_to(guild=MY_GUILD)
        try:
            print(f"Attempting to sync commands to guild {GUILD_ID} (application_id={getattr(self, 'application_id', None)})")

            # Diagnostics: fetch guild from API
            try:
                guild = await self.fetch_guild(GUILD_ID)
                print(f"fetch_guild succeeded: {guild.id} ({guild.name})")
            except discord.errors.Forbidden:
                print("fetch_guild: Forbidden (Missing Access)")
            except discord.errors.NotFound:
                print("fetch_guild: NotFound (Unknown Guild)")
            except Exception as e:
                print(f"fetch_guild error: {e}")

            # Check cache
            found = any(getattr(g, 'id', None) == GUILD_ID for g in self.guilds)
            print(f"Guild present in client.guilds cache: {found}")

            await self.tree.sync(guild=MY_GUILD)
            print(f"Successfully synced commands to guild {GUILD_ID}")
        except discord.errors.Forbidden:
            print(f"Warning: Missing access when syncing commands to guild {GUILD_ID}. Ensure the bot is in the guild and has the applications.commands scope and required permissions.")
            # fallback to global sync
            try:
                print("Falling back to global sync (may take up to an hour to propagate)")
                await self.tree.sync()
                print("Global sync complete")
            except Exception as e:
                print(f"Global sync failed: {e}")
        except Exception as e:
            print(f"Unexpected error while syncing commands: {e}")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Guilds (cached):', [g.id for g in self.guilds])

    async def on_message(self, message: discord.Message):
        # keep classic message handlers working
        if message.author == self.user:
            return

        content = message.content
        if content.startswith('meow'):
            await message.channel.send('BaBaBooey')
        elif content.startswith('cat'):
            await message.channel.send('cheeseburger')
        elif content.startswith('<:wawa_cat:1421035275886530581>'):
            await message.channel.send('<:wawa_cat:1421035275886530581>')
        elif content.startswith('<@1418488299500339322>'):
            await message.channel.send('<@1287082676339216386>')
        elif content.startswith('Developer') or content.startswith('開發者'):
            await message.channel.send('Developed by Niko(freeeeeeeeeman3)')
        elif content.startswith('mewing'):
            await message.channel.send('https://tenor.com/view/cat-gif-11905852304112868072')
        elif content.startswith('spam'):
            # send three callback buttons in one message
            def make_callback(reply_text: str):
                async def callback(interaction: discord.Interaction):
                    await interaction.response.send_message(reply_text, ephemeral=False)

                return callback

            view = discord.ui.View()
            btn1 = discord.ui.Button(label='spam', style=discord.ButtonStyle.primary)
            btn1.callback = make_callback('BaBaBooey')
            btn2 = discord.ui.Button(label='truth', style=discord.ButtonStyle.success)
            btn2.callback = make_callback('https://cdn.discordapp.com/attachments/1263134967794499645/1397476477314011188/IMG_20250708_195323.jpg?ex=6881dce4&is=68808b64&hm=7cd28ea2a0e835cc8f77c3b9a4dcbef4dd72303ded259e14bde0e937fd4eb24f&')
            btn3 = discord.ui.Button(label='lie', style=discord.ButtonStyle.danger)
            btn3.callback = make_callback('https://cdn.discordapp.com/attachments/1263134967794499645/1395064862924869642/IMG_20250708_195343.jpg?ex=687916e6&is=6877c566&hm=959022e41463d7c0fe4dcc460acd388b85a6b5178b44de1d8d10915a079e8f66&')

            view.add_item(btn1)
            view.add_item(btn2)
            view.add_item(btn3)

            # show typing indicator, wait, then send the view so it behaves like a natural response
            async with message.channel.typing():
                await asyncio.sleep(5)

            await message.channel.send('請選擇一個按鈕：', view=view)
        else:
            await message.channel.send('idk wdym')
            return

# --- Setup intents and client ---
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

# The classic ext commands bridge has been removed. Instead, `ping` is handled
# as a keyword in on_message (see below).

# --- Slash commands ---
@client.tree.command(name='spam')
@app_commands.describe(count='重複次數 (1~20)')
async def spam(interaction: discord.Interaction, count: app_commands.Range[int, 1, 20] = 10):
    """Bababooey"""
    await interaction.response.send_message(f'Bababooey<:wawa_cat:1421035275886530581>\\nspawn by {interaction.user.mention}')
    for i in range(count-1):
        await interaction.followup.send('Bababooey<:wawa_cat:1421035275886530581>')

# Optional: expose the ext bot's commands to the client loop
# This makes the ext commands (like !ping) usable; depending on your use-case you may not need this
# note: no ext_bot bridge; message-based keyword handlers are used instead

# --- Run ---
if __name__ == '__main__':
    try:
        keep_alive()
        client.run(TOKEN)
    except KeyboardInterrupt:
        print('Shutting down')
        sys.exit(0)
    except discord.HTTPException as e:
        if e.status == 429:
            print("The Discord servers denied the connection for making too many requests")
            print("Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests")
        else:
            raise e