from discord import embeds
from discord.ext import commands
from utils import discord_utils, logging_utils, admin_utils
import constants
import discord
from typing import Union


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ChannelManagementCog(commands.Cog, name="Channel Management"):
    """Set of channel management commands."""
    def __init__(self, bot):
        self.bot = bot

    @admin_utils.is_verified()
    @commands.command(name="movechannel")
    async def movechannel(self, ctx, *args):
        """Command to move the current channel to category with given name

        Usage: `~movechannel category name`"""
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

    @admin_utils.is_verified()
    @commands.command(name="renamechannel")
    async def renamechannel(self, ctx, *args):
        """Changes current channel name to whatever is asked

        Usage: `~renamechannel newname`"""
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

    @admin_utils.is_verified()
    @commands.command(name="createchannel", aliases=['makechannel',
                                                     'makechan',
                                                     'createchan'])
    async def createchannel(self, ctx, name: str):
        """Command to create channel in same category with given name

        Usage: `~createchannel new-channel-name`"""
        # log command in console
        logging_utils.log_command("createchannel", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # Category channel limit
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.")
            await ctx.send(embed=embed)
            return None

        channel = await discord_utils.createchannelgeneric(ctx.guild, ctx.channel.category, name)
        # Send status (success or fail)
        if channel:
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"Created channel {channel.mention} in `{channel.category.name}`!")
        else:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
        await ctx.send(embed=embed)

    @admin_utils.is_verified()
    @commands.command(name="clonechannel")
    async def clonechannel(self, ctx, original: str, new: str):
        """Command to create channel in same category with given name

        Usage: `~clonechannel #channel-to-clone new-channel-name`"""
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


    @admin_utils.is_verified()
    @commands.command(name="clonecategory", aliases=["copycategory"])
    async def clonecategory(self, ctx, origCatName: str, targetCatName: str, origRole: Union[discord.Role, str] = None, targetRole: Union[discord.Role, str] = None):
        """Clones origCatName as targetCatName. OPTIONAL: takes origRole's perms and makes those targetRole's perms in targetCat.
        Creates targetCat (optional: targetRole) if they don't exist already.
        
        Usage: `~clonecategory 'Puzzlehunt Team A' 'Puzzlehunt Team B' @PuzzlehuntTeamA @PuzzlehuntTeamB`"""
        logging_utils.log_command("clonecategory", ctx.channel, ctx.author)
        embed = discord.Embed(description="", color=constants.EMBED_COLOR)

        # Input parsing I guess
        # First, make sure origCat exists
        origCat = discord.utils.get(ctx.guild.channels, name=origCatName)
        if origCat is None:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"I cannot find category {origCatName}. Perhaps check your spelling and try again.")
            await ctx.send(embed=embed)
            return
        # Either neither origRole nor targetRole are supplied, or both are. If XOR, that's a fail.
        if origRole is not None and targetRole is None or origRole is None and targetRole is not None:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"Next time, please supply both `origRole` and `targetRole`, or neither.")
            await ctx.send(embed=embed)
            return
        
        # Next, make sure that origRole exists (and find if targetRole exists, otherwise create it)
        # If the user didn't supply roles, ignore this part.
        if origRole is None:
            origRole_is_str = isinstance(origRole, str)
            targetRole_is_str = isinstance(targetRole, str)
            if origRole_is_str or targetRole_is_str:
                # Get role
                guild_roles = await ctx.guild.fetch_roles()
                for role in guild_roles:
                    origRole_is_str = isinstance(origRole, str)
                    targetRole_is_str = isinstance(targetRole, str)
                    # Once both are actual discord roles, get out of here
                    if not origRole_is_str and not targetRole_is_str:
                        break
                    if origRole_is_str and role.name.lower() == origRole.lower():
                        origRole = role
                    if targetRole_is_str and role.name.lower() == targetRole.lower():
                        targetRole = role
            # If we have looped over all the roles and still can't find an origRole, then that's an error
            if origRole_is_str:
                embed.add_field(name=f"{constants.FAILED}",
                                value=f"Cannot find role {origRole}, are you sure it exists? Retry this command with @{origRole} " + 
                                    f"if it does.")
                await ctx.send(embed=embed)
                return

            # if targetRole doesn't exist, create it
            if targetRole_is_str:
                try:
                    targetRole = await ctx.guild.create_role(name=targetRole, mentionable=True)
                    embed.description += f"\nCreated {targetRole.mention}"
                except discord.Forbidden:
                    embed.add_field(name=f"{constants.FAILED}",
                                    value=f"I was unable to create role {targetRole}. Do I have the `manage_roles` permission?")
                    await ctx.send(embed=embed)
                    return
        
        # if targetCat doesn't exist, create it
        targetCat = discord.utils.get(ctx.guild.channels, name=targetCatName)
        try:
            if targetCat is None:
                targetCat = await origCat.clone(name=targetCatName)
                embed.description += f"\nCloned `{origCat}` as `{targetCat}`"
            if origRole is not None:
                if origRole in origCat.overwrites:
                    await targetCat.set_permissions(targetRole, overwrite=origCat.overwrites[origRole])
                    await targetCat.set_permissions(origRole, overwrite=None)
                    embed.description += f"\nSynced {targetRole.mention}'s permissions in `{targetCat}` with " + \
                                        f"{origRole.mention}'s in `{origCat}`"
                else:
                    embed.description += f"\n{origRole.mention} does not seem to have permission overwrites in `{origCat}`"
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"I was unable to create category {targetCatName}. Do I have the `manage_channels` permission?")
            await ctx.send(embed=embed)
            return

        embed.title = f"{constants.SUCCESS}"
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))
