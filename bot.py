import os
import json
import discord
from discord.ext import commands
from utils import discord_utils
from dotenv.main import load_dotenv
load_dotenv(override=True)
import constants
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')


def get_prefix(client, message):
    with open(constants.PREFIX_JSON_FILE, 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]


def main():
    intents = discord.Intents.default()
    client = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    @client.event
    async def on_ready():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you solve👀 |~help"))
        # Keep a json file of all the servers the bot is in and what command prefix to use for them.
        if not os.path.exists(os.path.join(os.getcwd(), constants.PREFIX_JSON_FILE)):
            with open(constants.PREFIX_JSON_FILE, 'w') as f:
                json.dump({}, f)
        # Read in the prefix file, then check if the guild is in it.
        with open(constants.PREFIX_JSON_FILE, 'r') as f:
            prefixes = json.load(f)
        for guild in client.guilds:

            if str(guild.id) not in prefixes:
                prefixes[str(guild.id)] = constants.DEFAULT_BOT_PREFIX
                print(f"Added {constants.DEFAULT_BOT_PREFIX} as prefix in {guild}")

            print(f"{client.user.name} has connected to the following guild: {guild.name} (id: {guild.id}) with prefix {prefixes[str(guild.id)]}")
        with open(constants.PREFIX_JSON_FILE, 'w') as f:
            json.dump(prefixes, f)

    @client.event
    async def on_message(message):
        if client.user.mentioned_in(message):
            print("I have been mentioned")
            with open(constants.PREFIX_JSON_FILE, 'r') as f:
                prefixes = json.load(f)
            pre = prefixes[str(message.guild.id)]

            embed = discord_utils.create_embed()
            embed.add_field(name="Prefix",
                            value=f"My prefix in this server is \"{pre}\". Use {pre}help "
                                  f"to learn about my commands!",
                            inline=False)
            await message.channel.send(embed=embed)

        await client.process_commands(message)

    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
