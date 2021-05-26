import constants
import discord
from discord.ext import commands
from utils import discord_utils
from modules.channel_management import channel_management_utils


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
    @commands.has_any_role(
        constants.TA_VERIFIED_PUZZLER_ROLE_ID,
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def movechannel(self, ctx, *args):
        """Command to move channel to category with given name"""
        print("Received movechannel")
        embed = discord_utils.create_embed()
        # check for category name arguments
        if len(args) <= 0:
            discord_utils.create_no_argument_embed("Category")
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

        if len(new_category.channels) >= 50:
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
    @commands.has_any_role(*constants.VERIFIEDS["Verified"])
    async def renamechannel(self, ctx, *args):
        """Changes current channel name to whatever is asked
        Usage: ~renamechannel Newname"""
        # log command in console
        embed = discord_utils.create_embed()
        print("Received renamechannel")
        if len(args) <= 0:
            embed.add_field(name=f"{constants.FAILED}!", value=f"You must specify a new channel name!")
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
    @commands.has_any_role(
        constants.TA_VERIFIED_PUZZLER_ROLE_ID,
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def createchannel(self, ctx, name: str = ""):
        """Wrapper function for createchannel for self calls"""
        """Command to create channel in same category with given name"""
        # log command in console
        print("Received createchannel")

        embed = discord_utils.create_embed()

        channel, embed = await channel_management_utils.createchannelgeneric(ctx.guild, ctx.channel.category, name)
        # Send status (success or fail)
        await ctx.send(embed=embed)

    @commands.command(name="clonechannel")
    @commands.has_any_role(
        constants.TA_VERIFIED_PUZZLER_ROLE_ID,
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def clonechannel(self, ctx, original: str, new: str):
        """Command to create channel in same category with given name"""
        # log command in console
        print("Received clonechannel")
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

        if len(category.channels) >= 50:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{category.name}` is already full, max limit is 50 channels.")
            # reply to user
            await ctx.send(embed=embed)
            return

        # TODO: use genericcreatechannel from channel_management_utils
        try:
            # create channel
            new_channel = await guild.create_text_channel(new, category=category, overwrites=old_channel.overwrites)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return
        
        embed.add_field(name="Success!", value=f"Created channel {new_channel.mention} in {category}!")
        # reply to user
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))
