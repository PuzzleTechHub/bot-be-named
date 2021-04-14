import constants
from discord.ext import commands
from utils import discord_utils


class CloneChannelCog(commands.Cog, name="Create Channel"):
    """Checks for `clonechannel` command
    Clones channel in same category with given name"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clonechannel")
    @commands.has_any_role(
        constants.VERIFIED_PUZZLER,
        constants.TA_VERIFIED_PUZZLER_ROLE_ID
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
    bot.add_cog(CloneChannelCog(bot))
