from discord.ext import commands
from utils import discord_utils, logging_utils
import constants
import discord


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ChannelManagementCog(commands.Cog, name="Channel Management"):
    """Set of channel management commands.
        - create channel
        - move channel
        - rename channel
        - clone channel
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="movechannel")
    @commands.has_any_role(*constants.VERIFIED)
    async def movechannel(self, ctx, *args):
        """Command to move channel to category with given name"""
        logging_utils.log_command("movechannel", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        # check for category name arguments
        if len(args) <= 0:
            embed = discord_utils.create_no_argument_embed("Category")
            await ctx.send(embed=embed)
            return

        # join arguments to form channel name
        category_name = " ".join(args)
        # get current channel
        channel = ctx.channel
        # get new category
        new_category = discord.utils.get(ctx.guild.channels, name=category_name)

        if new_category is None:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Could not find category `{category_name}`")
            # reply to user
            await ctx.send(embed=embed)
            return

        if discord_utils.category_is_full(new_category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{new_category.name}` is already full, max limit is 50 channels.")
            # reply to user
            await ctx.send(embed=embed)
            return

        try:
            # move channel
            await ctx.channel.edit(category=new_category)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"Moving {channel.mention} to {new_category.name}!")
        # reply to user
        await ctx.send(embed=embed)

    @commands.command(name="renamechannel")
    @commands.has_any_role(*constants.VERIFIED)
    async def renamechannel(self, ctx, *args):
        """Changes current channel name to whatever is asked
        Usage: ~renamechannel Newname"""
        # log command in console
        logging_utils.log_command("renamechannel", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        if len(args) <= 0:
            embed = discord_utils.create_no_argument_embed("Channel name")
            # reply to user
            await ctx.send(embed=embed)
            return

        channel = ctx.message.channel
        old_channel_name = channel.name
        new_channel_name = " ".join(args)

        try:
            # rename channel
            await channel.edit(name=new_channel_name)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"Renamed `{old_channel_name}` to `{new_channel_name}`: {channel.mention}!",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="createchannel", aliases=['makechannel',
                                                     'makechan',
                                                     'createchan'])
    @commands.has_any_role(*constants.VERIFIED)
    async def createchannel(self, ctx, name: str):
        """Command to create channel in same category with given name"""
        # log command in console
        logging_utils.log_command("createchannel", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # Category channel limit
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{ctx.category.name}` is already full, max limit is 50 channels.")
            return None, embed

        channel = await discord_utils.createchannelgeneric(ctx.guild, ctx.channel.category, name)
        # Send status (success or fail)
        if channel:
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Created channel {channel.mention} in `{channel.category.name}`!")
        else:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
        await ctx.send(embed=embed)

    @commands.command(name="clonechannel")
    @commands.has_any_role(*constants.VERIFIED)
    async def clonechannel(self, ctx, original: str, new: str):
        """Command to create channel in same category with given name"""
        # log command in console
        logging_utils.log_command("clonechannel", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # get guild and category
        guild = ctx.message.guild
        category = ctx.channel.category

        try:
            old_channel = discord_utils.find_channel(self.bot, guild.channels, original)
        except ValueError:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Channel `{original}` was not found.")
            # reply to user
            await ctx.send(embed=embed)
            return

        if discord_utils.category_is_full(category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{category.name}` is already full, max limit is 50 channels.")
            # reply to user
            await ctx.send(embed=embed)
            return

        # TODO: use genericcreatechannel from discord_utils?
        try:
            # create channel
            new_channel = await guild.create_text_channel(new, category=category, overwrites=old_channel.overwrites)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return
        
        embed.add_field(name=f"{constants.SUCCESS}!", value=f"Created channel {new_channel.mention} in {category}!")
        # reply to user
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))
