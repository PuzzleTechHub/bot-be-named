from discord import embeds
from discord.ext import commands
from utils import discord_utils, logging_utils, command_predicates
import constants
import discord
from typing import Union


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class ChannelManagementCog(commands.Cog, name="Channel Management"):
    """Set of channel and category management commands."""
    def __init__(self, bot):
        self.bot = bot

    ####################
    # CHANNEL COMMANDS #
    ####################

    @command_predicates.is_verified()
    @commands.command(name="movechannel")
    async def movechannel(self, ctx, category_name: str):
        """Command to move the current channel to category with given name

        Category : Verified Roles only.
        Usage: `~movechannel "Category name"`
        """
        logging_utils.log_command("movechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # get current channel
        channel = ctx.channel
        # get new category
        new_category = await discord_utils.find_category(ctx, category_name)

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

    @command_predicates.is_verified()
    @commands.command(name="renamechannel", aliases=["renamechan"])
    async def renamechannel(self, ctx, new_channel_name: Union[discord.TextChannel, str]):
        """Changes current channel name to whatever is asked

        Category : Verified Roles only.
        Usage: `~renamechannel newname`
        """
        # log command in console
        logging_utils.log_command("renamechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        #If user managed to tag a channel name instead of typing
        if not isinstance(new_channel_name, str):
            new_channel_name = new_channel_name.name
         
        old_channel_name = ctx.channel.name

        try:
            # rename channel
            await ctx.channel.edit(name=new_channel_name)
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"Renamed `{old_channel_name}` to `{new_channel_name}`: {ctx.channel.mention}!",
                        inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="createchannel", aliases=["makechannel", "makechan", "createchan"])
    async def createchannel(self, ctx, name: str):
        """Command to create channel in same category with given name

        Category : Verified Roles only.
        Usage: `~createchannel new-channel-name`
        """
        # log command in console
        logging_utils.log_command("createchannel", ctx.guild, ctx.channel, ctx.author)
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

    @command_predicates.is_verified()
    @commands.command(name="clonechannel")
    async def clonechannel(self, ctx, original: Union[discord.TextChannel, str], new: str):
        """Command to create channel in same category with given name

        Category : Verified Roles only.
        Usage: `~clonechannel #channel-to-clone new-channel-name`
        """
        # log command in console
        logging_utils.log_command("clonechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # get guild and category
        guild = ctx.message.guild
        category = ctx.channel.category

        if isinstance(original, discord.TextChannel):
            old_channel = original
        else: 
            old_channel = await commands.TextChannelConverter().convert(ctx, original)

        if old_channel is None:
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

    #####################
    # CATEGORY COMMANDS #
    #####################

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="synccategory", aliases=["synccat","catsync"])
    async def synccategory(self, ctx):
        """Changes permissions of all channels in Current Category to be synced to Cat-permissions.
        So any channel with different role permissions set up is reverted.

        Category : Trusted Roles only.
        Usage: `~synccat`
        """
        logging_utils.log_command("synccategory", ctx.guild, ctx.channel, ctx.author)
        
        category = ctx.channel.category
        
        start_embed = discord_utils.create_embed()
        start_embed.add_field(name="Sync Started",
                        value=f"Your syncing of category `{category.name}`"
                              f" has begun! This may take a while. If I run into "
                              f"any errors, I'll let you know.",
                        inline=False)
        start_msg = await ctx.send(embed=start_embed)

        try:
            for channel in category.channels:
                await channel.edit(sync_permissions=True)
        except discord.Forbidden:
            if start_msg:
                await start_msg.delete()
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            # reply to user
            await ctx.send(embed=embed)
            return

        if start_msg:
            await start_msg.delete()
        embed = discord_utils.create_embed()
        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"All channels in category `{category.name}` successfully synced to Category!")
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="movecategory", aliases=["movecat"])
    async def movecategory(self, ctx, cat_a_name: str, cat_b_name: str = ""):
        """Moves a category to below another category.

        Category : Verified Roles only.
        Usage: `~movecat 'Category A' 'Category B'` (Moves Cat A to just below Cat B)
        Usage: `~movecat 'Category B'` (Moves the current category to just below Category B)
        """
        logging_utils.log_command("movecategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord.Embed(description="", color=constants.EMBED_COLOR)

        cat_a = await discord_utils.find_category(ctx, cat_a_name)
        if cat_a is None:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"I cannot find category {cat_a_name}. Perhaps check your spelling and try again.")
            await ctx.send(embed=embed)
            return

        if(cat_b_name==""):
            curr_cat = ctx.channel.category
            if curr_cat is None:
                embed.add_field(name=f"{constants.FAILED}",
                                value=f"The current channel {ctx.channel} does not exist in a category I can move. Check `~help movecat`.")
                await ctx.send(embed=embed)
                return
            try:
                await curr_cat.edit(position=cat_a.position+1)
                embed.title = f"{constants.SUCCESS}"
                embed.description += f"\nMoved `{curr_cat}` to just below `{cat_a}` in the server"
            except discord.Forbidden:
                embed.add_field(name=f"{constants.FAILED}",
                                value=f"I was unable to move category `{curr_cat}`. Do I have the `manage_channels` permission?")
                await ctx.send(embed=embed)
                return
            await ctx.send(embed=embed)
            return

        cat_b = await discord_utils.find_category(ctx, cat_b_name)
        if cat_b is None:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"I cannot find category `{cat_b_name}`. Perhaps check your spelling and try again.")
            await ctx.send(embed=embed)
            return
              
        try:
            await cat_a.edit(position=cat_b.position+1)
            embed.title = f"{constants.SUCCESS}"
            embed.description += f"\nMoved `{cat_a}` to just below `{cat_b}` in the server"
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"I was unable to move category `{cat_a}`. Do I have the `manage_channels` permission?")
            await ctx.send(embed=embed)
            return
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="clonecategory", aliases=["copycategory","clonecat","copycat"])
    async def clonecategory(self, ctx, origCatName: str, targetCatName: str, origRole: Union[discord.Role, str] = None, targetRole: Union[discord.Role, str] = None):
        """Clones one category as another. 
        OPTIONAL: takes origRole's perms and makes those targetRole's perms in targetCat.
        Creates targetCat (and targetRole, if specified) if they don't exist already.
        
        Category : Verified Roles only.
        Usage: `~clonecategory 'Category A' 'Category B'` (clones Cat A as Cat B)
        Usage: `~clonecategory 'Category A' 'Category B' @RoleC @RoleD` (clones Cat A as Cat B. Clones RoleC permission on Cat A, and replicates it with RoleD and Cat B)
        """
        logging_utils.log_command("clonecategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord.Embed(description="", color=constants.EMBED_COLOR)

        # Input parsing I guess
        # First, make sure origCat exists
        origCat = await discord_utils.find_category(ctx, origCatName)
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
        origRole_is_str = isinstance(origRole, str)
        targetRole_is_str = isinstance(targetRole, str)

        if origRole_is_str or targetRole_is_str:
            # Get role
            guild_roles = await ctx.guild.fetch_roles()
            for role in guild_roles:
                # Once both are actual discord roles, get out of here
                if not origRole_is_str and not targetRole_is_str:
                    break
                if origRole_is_str and role.name.lower() == origRole.lower():
                    origRole = role
                if targetRole_is_str and role.name.lower() == targetRole.lower():
                    targetRole = role

        origRole_is_str = isinstance(origRole, str)
        targetRole_is_str = isinstance(targetRole, str)

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
        targetCat = await discord_utils.find_category(ctx, targetCatName)
        try:
            if targetCat is None:
                targetCat = await origCat.clone(name=targetCatName)
                embed.description += f"\nCloned `{origCat}` as `{targetCat}`"
                await targetCat.edit(position=origCat.position+1)
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

    @command_predicates.is_owner_or_admin()
    @commands.command(name="listcategories", aliases=["lscategories", "listcats", "lscats", "listcat", "lscat"])
    async def listcategories(self, ctx):
        """List all the categories in a server

        Category : Admin and Bot Owner only.        
        Usage: `~listcat`
        """
        logging_utils.log_command("listcategories", ctx.guild, ctx.channel, ctx.author)
        categories = [cat.name for cat in ctx.guild.categories]
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Categories in {ctx.guild.name}",
                        value=f"{chr(10).join(categories)}")
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="categorysort", aliases=["sortcat", "catsort", "sortcategory", "reorderchannels"])
    async def categorysort(self, ctx):
        """Sort all channels in a category. Specifically for puzzle hunts, `solved-`, `backsolved-`, and `solvedish-` 
        prefixes will be put behind channels without a prefix.

        Category : Verified Roles only.
        Usage: `~categorysort`
        """
        logging_utils.log_command("categorysort", ctx.guild, ctx.channel, ctx.author)

        channel_list = discord_utils.sort_channels_util(ctx.channel.category.text_channels)

        start_embed = discord_utils.create_embed()
        start_embed.add_field(name=f"Sort Started",
                              value=f"Your sort of category `{ctx.channel.category}` has begun! "
                                    f"This may take a while. If I run into any errors, I'll let you know.")
        start_embed_msg = await ctx.send(embed=start_embed)

        for idx, channel in enumerate(channel_list):
            # Skip channels already in correct place.
            if channel.position == idx:
                continue
            try:
                await channel.edit(position=idx)
            except discord.Forbidden:
                if start_embed_msg:
                    await start_embed_msg.delete()
                embed = discord_utils.create_embed()
                embed.add_field(name=f"{constants.FAILED}!",
                                value=f"Unable to sort `{channel.mention}`. Do I have the correct `manage_channel` positions?")
                await ctx.send(embed=embed)
                return
        
        if start_embed_msg:
            await start_embed_msg.delete()
        embed = discord_utils.create_embed()
        embed.add_field(name=f"{constants.SUCCESS}!",
                        value=f"Sorted the channels in `{ctx.channel.category}`!")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))
