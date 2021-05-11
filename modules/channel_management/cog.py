import constants
import discord
from discord.ext import commands
from utils import discord_utils

# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ChannelManagementCog(commands.Cog, name="Channel Management"):
    """Checks for `movechannel` command
    Moves current channel to given category"""

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
            embed.add_field(name=f"{constants.FAILED}!", value=f"You must specify a category!")
            # reply to user
            await ctx.send(embed=embed)
            return 0

        # join arguments to form channel name
        category_name = " ".join(args)
        # get current channel
        channel = ctx.channel
        # get new category
        new_category = discord.utils.get(ctx.guild.channels, name=category_name)

        if new_category is None:
            embed.add_field(name=f"{constants.FAILED}!", value=f"Could not find category `{category_name}`")
            # reply to user
            await ctx.send(embed=embed)
            return 0

        if len(new_category.channels)>=50:
            embed.add_field(name=f"{constants.FAILED}!", value=f"Category `{category_name}` is already full, max limit is 50 channels.")
            # reply to user
            await ctx.send(embed=embed)
            return 0

        embed.add_field(name=f"{constants.SUCCESS}!", value=f"Moving {channel.mention} to {new_category}!")
        # reply to user
        await ctx.send(embed=embed)
        # move channel
        await ctx.channel.edit(category=new_category)
        

    @commands.command(name="createchannel")
    @commands.has_any_role(
        constants.TA_VERIFIED_PUZZLER_ROLE_ID,
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def createchannel(self, ctx, name: str = ""):
        """Command to create channel in same category with given name"""
        # log command in console
        print("Received createchannel")
        embed = discord_utils.create_embed()
        # no argument passed
        if len(name) <= 0:
            embed.add_field(name="Failed!", value=f"You must specify a channel name!")
            # reply to user
            await ctx.send(embed=embed)
            return
        # get guild and category
        guild = ctx.message.guild
        category = ctx.channel.category
        # create channel
        channel = await guild.create_text_channel(name, category=category)
        embed.add_field(name="Success!", value=f"Created channel {channel.mention} in {category}!")
        # reply to user
        await ctx.send(embed=embed)

    @commands.command(name="clonechannel")
    @commands.has_any_role(
        constants.TA_VERIFIED_PUZZLER_ROLE_ID,
        constants.SONI_SERVER_TESTER_ROLE,
        constants.KEV_SERVER_TESTER_ROLE
    )
    async def clonechannel(self, ctx, original: str = "", new: str = ""):
        """Command to create channel in same category with given name"""
        # log command in console
        print("Received clonechannel")
        embed = discord_utils.create_embed()
        # no argument passed
        if len(original) <= 1:
            embed.add_field(name="Failed!", value=f"You must specify a channel to clone and the new channel name!")
            # reply to user
            await ctx.send(embed=embed)
            return
        # get guild and category
        guild = ctx.message.guild
        category = ctx.channel.category
        old_channel = discord_utils.find_channel(self.bot, guild.channels, original)
        # create channel
        new_channel = await guild.create_text_channel(new, category=category, overwrites=old_channel.overwrites)

        
        embed.add_field(name="Success!", value=f"Created channel {new_channel.mention} in {category}!")
        # reply to user
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))