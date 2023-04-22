from nextcord import embeds
from nextcord.ext import commands
from utils import discord_utils, logging_utils, command_predicates
import constants
import nextcord
from typing import Union
import asyncio
from modules.solved import solved_constants

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
    @commands.command(name="movechan", aliases=["movechannel"])
    async def movechannel(
        self, ctx, category_name: str, *args: Union[nextcord.TextChannel, str]
    ):
        """Command to move channels to category with given name

        Permission Category : Verified Roles only.
        Usage: `~movechannel "CatA"` (Moves current channel to CatA)
        Usage: `~movechannel "CatA" #chan1 "chan2" "chan3"` (Moves all listed channels to CatA. Note - This does not move current channel unless listed)
        Usage: `~movechannel "CatA" all` (Moves all channels in current category to CatA.)

        Note that channels may be mentioned or named, but a channel is named "all", then it must be mentioned to avoid issues.
        """
        logging_utils.log_command("movechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # get current channel
        channel = ctx.channel
        # get new category
        new_category = await discord_utils.find_category(ctx, category_name)

        if new_category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Could not find category `{category_name}`",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        channelstomove = []

        # No arg given. Move only current channel
        if len(args) == 0:
            channelstomove.append(channel)
        # Only one arg given, "All". Move all channels in category
        elif len(args) == 1 and args[0] == "all":
            for chan in ctx.channel.category.channels:
                channelstomove.append(chan)
        # One or more args given. All processed as channels.
        else:
            # Process as N channels then add
            for unclean_chan in args:
                if isinstance(unclean_chan, nextcord.TextChannel):
                    chan = unclean_chan
                else:
                    embed.add_field(
                        name="Error Finding Channel!",
                        value=f"Could not find channel `{unclean_chan}`. Perhaps check your spelling and try again.",
                        inline=False,
                    )
                    continue
                channelstomove.append(chan)

        channels_moved = []
        for chan in channelstomove:
            if chan.category == new_category:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"Channel {chan.mention} is already in Category `{new_category.name}`.",
                    inline=False,
                )
                continue
            if discord_utils.category_is_full(new_category):
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"Could not move channel {chan.mention}. Category `{new_category.name}` is already full, max limit is 50 channels.",
                    inline=False,
                )
                continue
            # Move the channels
            try:
                await chan.edit(category=new_category)
                channels_moved.append(chan)
            except nextcord.Forbidden:
                embed.insert_field_at(
                    0,
                    name=f"{constants.FAILED}!",
                    value=f"Forbidden! Have you checked if the bot has the required permisisons?",
                    inline=False,
                )
                # reply to user
                await ctx.send(embed=embed)
                return

        if len(channels_moved) < 1:
            embed.insert_field_at(
                0,
                name="Complete!",
                value=f"Did not move any channels to `{new_category.name}`.",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Moved these channels to `{new_category.name}` : {', '.join([chan.mention for chan in channels_moved])}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="renamechan", aliases=["renamechannel", "renamethread"])
    async def renamechannel(
        self,
        ctx,
        chan_a: Union[nextcord.TextChannel, nextcord.Thread, str],
        chan_b: Union[nextcord.TextChannel, nextcord.Thread, str] = "",
    ):
        """Changes current channel name to whatever is asked.

        Permission Category : Verified Roles only.
        Usage: `~renamechannel newname` (Renames current channel)
        Usage: `~renamechan #old-chan newname`

        Can rename threads as well.

        Note that if you use more than 2 channel renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes.
        Those channels will have to be renamed manually, or wait for the full 10 mins.
        """
        # log command in console
        logging_utils.log_command("renamechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if chan_b == "":
            old_channel_name = ctx.channel.name
            new_channel_name = chan_a
        else:
            old_channel_name = chan_a
            new_channel_name = chan_b

        old_channel = await discord_utils.find_chan_or_thread(ctx, old_channel_name)
        if old_channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Channel `{old_channel_name}` was not found.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        # If user managed to tag a channel name instead of typing
        if not isinstance(new_channel_name, str):
            new_channel_name = new_channel_name.name

        try:
            # rename channel
            await old_channel.edit(name=new_channel_name)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Renamed `{old_channel_name}` to `{new_channel_name}`: {ctx.channel.mention}!",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="makethread", aliases=["createthread"])
    async def createthread(self, ctx, name: str):
        """Command to create thread in same category with given name

        Permission Category : Verified Roles only.
        Usage: `~createthread new-thread-name`
        """
        # log command in console
        logging_utils.log_command("createthread", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        channel = await discord_utils.createthreadgeneric(
            ctx.message, ctx.channel, name
        )
        # Send status (success or fail)
        if channel:
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Created channel {channel.mention} in `{channel.category.name}`!",
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="createchan", aliases=["makechannel", "makechan", "createchannel"]
    )
    async def createchannel(self, ctx, name: str):
        """Command to create channel in same category with given name

        Permission Category : Verified Roles only.
        Usage: `~createchannel new-channel-name`
        """
        # log command in console
        logging_utils.log_command("createchannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # Category channel limit
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.",
            )
            await ctx.send(embed=embed)
            return None

        channel = await discord_utils.createchannelgeneric(
            ctx.guild, ctx.channel.category, name
        )
        # Send status (success or fail)
        if channel:
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"Created channel {channel.mention} in `{channel.category.name}`!",
            )
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="clonechan", aliases=["clonechannel", "chanclone"])
    async def clonechannel(
        self,
        ctx,
        chan_a: Union[nextcord.TextChannel, str],
        chan_b: str = "",
        origRoleorUser: Union[nextcord.Role, nextcord.Member, str] = None,
        targetRoleorUser: Union[nextcord.Role, nextcord.Member, str] = None,
    ):
        """Command to create channel in same category with given name.
        If user/role is specified, then syncs permissions as well.
        The channel created is just below the channel being cloned

        If making role/user changes, both old channel and new channel is necessary.

        Permission Category : Verified Roles only.
        Usage: `~clonechannel #channel-to-clone new-channel-name`
        Usage: `~clonechannel new-channel-name` (Clones current channel)
        Usage: `~clonechannel #chan1 chan2 @roleA @userB` (clones then syncs permission of A in chan1 with B in chan2)
        """
        # log command in console
        logging_utils.log_command("clonechannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if chan_b == "":
            old_channel_name = ctx.channel
            new_channel_name = chan_a
        else:
            old_channel_name = chan_a
            new_channel_name = chan_b

        old_channel = await discord_utils.find_chan_or_thread(ctx, old_channel_name)

        if old_channel is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Channel `{old_channel_name}` was not found.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        if isinstance(origRoleorUser, str):
            origUser = await discord_utils.find_user(ctx, origUser)
            if origUser is None:
                origRole = await discord_utils.find_role(ctx, origRoleorUser)
                if origRole is None:
                    embed.add_field(
                        name=f"{constants.FAILED}!",
                        value=f"Role/User `{origRoleorUser}` does not exist. Please use @ to tag them.",
                    )
                    # reply to user
                    await ctx.send(embed=embed)
                    return
                else:
                    origRoleorUser = origRole
            else:
                origRoleorUser = origUser

        if isinstance(targetRoleorUser, str):
            targetUser = await discord_utils.find_user(ctx, targetRoleorUser)
            if targetUser is None:
                targetRole = await discord_utils.find_role(ctx, targetRoleorUser)
                if targetRole is None:
                    try:
                        targetRoleorUser = await ctx.guild.create_role(
                            name=targetRoleorUser
                        )
                        await targetRoleorUser.edit(mentionable=True)
                        embed.add_field(
                            name=f"Created role {targetRoleorUser}",
                            value=f"Could not find role `{targetRoleorUser}`, so I created it.",
                            inline=False,
                        )
                    except nextcord.Forbidden:
                        embed.add_field(
                            name=f"{constants.FAILED}!",
                            value=f"I couldn't find role `{targetRoleorUser}`, so I tried to make it. But I don't have "
                            f"permission to add a role in this server. Do I have the `add_roles` permission?",
                            inline=False,
                        )
                        await ctx.send(embed=embed)
                        return
                else:
                    targetRoleorUser = targetRole
            else:
                targetRoleorUser = targetUser

        # get guild and category
        guild = old_channel.guild
        category = old_channel.category

        if discord_utils.category_is_full(category):
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Category `{category.name}` is already full, max limit is 50 channels.",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        try:
            # create channel
            new_channel = await guild.create_text_channel(
                new_channel_name, category=category, overwrites=old_channel.overwrites
            )
            await new_channel.edit(position=old_channel.position + 1)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Created channel {new_channel.mention} in `{category}` as a clone of {old_channel.mention}!",
            inline=False,
        )

        # If roles exist, add them.
        if origRoleorUser and targetRoleorUser:
            overwrites = old_channel.overwrites
            if overwrites.get(origRoleorUser) is None:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"{origRoleorUser.mention} is not in {old_channel.mention} overwrites. Skipping!",
                    inline=False,
                )
            else:
                try:
                    overwrite = overwrites.get(origRoleorUser)
                    await new_channel.set_permissions(origRoleorUser, overwrite=None)
                    await new_channel.set_permissions(
                        targetRoleorUser, overwrite=overwrite
                    )
                    embed.add_field(
                        name=f"{constants.SUCCESS}!",
                        value=f"Synced permissions of {origRoleorUser.mention} in {old_channel.mention} with that of {targetRoleorUser.mention} in {new_channel.mention}.",
                        inline=False,
                    )
                except nextcord.Forbidden:
                    embed.add_field(
                        name=f"{constants.FAILED}!",
                        value=f"Forbidden! Have you checked if the bot has the required permisisons?",
                        inline=False,
                    )
                    # reply to user
                    await ctx.send(embed=embed)
                    return

        # reply to user
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="shiftchan", aliases=["shiftchannel"])
    async def shiftchannel(
        self,
        ctx,
        chan_a_name: Union[nextcord.TextChannel, str],
        chan_b_name: Union[nextcord.TextChannel, str] = "",
    ):
        """Shifts a channel to below another channel in the same category.

        Does not work for Voice Channels, just Text Channels.
        Channels may be mentioned or named, but better to mention (in case of multiple channels with same name).

        Note : Use "0" or "top" instead to say "Top of the category". But if a channel in the server is named #top or #0 then the respective argument wont work
        Permission Category : Verified Roles only.
        Usage: `~shiftchan #chana #chanb` (Shifts Chan A to just below Chan B)
        Usage: `~shiftchan "chanb"` (Shifts the current channel to just below Chan B)
        Usage: `~shiftchan "chana" top` (Shifts ChanA to top of category)
        Usage: `~shiftchan 0` (Shifts the current channel to top of category)
        """
        logging_utils.log_command("shiftchannel", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        pos_to_shift_to = -1
        chan_to_shift = None

        if chan_b_name == "" and chan_a_name in ["top", "0"]:
            # Shift CurrChan to top
            chan_to_shift = ctx.channel
            pos_to_shift_to = 0
        elif chan_b_name in ["top", "0"]:
            # Shift Chan A to top
            chan_to_shift = chan_a_name
            pos_to_shift_to = 0
        else:
            if chan_b_name == "":
                # Shift CurrChan to ChanA
                chan_to_shift = ctx.channel
                chan_shifting_to = chan_a_name
            else:
                # Shift ChanA to ChanB
                chan_to_shift = chan_a_name
                chan_shifting_to = chan_b_name

        if not isinstance(chan_to_shift, nextcord.TextChannel):
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I cannot find channel `{chan_to_shift}`. Perhaps check your spelling and try again.",
            )
            await ctx.send(embed=embed)
            return

        # Not top, so position needs to be given
        if pos_to_shift_to == -1:
            if not isinstance(chan_shifting_to, nextcord.TextChannel):
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I cannot find channel `{chan_shifting_to}`. Perhaps check your spelling and try again.",
                )
                await ctx.send(embed=embed)
                return
            if chan_shifting_to.category != chan_to_shift.category:
                # Different categories for channel to shift to
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"The channel to be shifted {chan_to_shift.mention} is in category `{chan_to_shift.category}` but it's trying to shift to channel {chan_shifting_to.mention}, which is in category `{chan_shifting_to.category}`"
                    f"\nUse `~movechan` to move the channel across categories first.",
                )
                await ctx.send(embed=embed)
                return
            # No errors
            pos_to_shift_to = chan_shifting_to.position + 1

        # Move channels
        try:
            await chan_to_shift.edit(position=pos_to_shift_to)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
            await ctx.send(embed=embed)
            return

        if pos_to_shift_to == 0:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Succesfully moved channel {chan_to_shift.mention} to top of category {chan_to_shift.category}",
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Succesfully moved channel {chan_to_shift.mention} to just below {chan_shifting_to.mention}",
            )
        await ctx.send(embed=embed)

    ##########################
    # VOICE CHANNEL COMMANDS #
    ##########################

    @command_predicates.is_verified()
    @commands.command(name="renamevc", aliases=["renamevoicechan", "renamevoice"])
    async def renamevoicechan(self, ctx, new_name: str):
        """Command to rename the Voice Channel in which the user currently is

        Permission Category : Verified Roles only.
        Usage: `~renamevc "VC-Name"`
        """
        # log command in console
        logging_utils.log_command("renamevoicechan", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        voice_chan_list = ctx.guild.voice_channels
        calling_user = ctx.author

        voice_chan_to_rename = None
        for vc in voice_chan_list:
            if calling_user in vc.members:
                voice_chan_to_rename = vc
                break

        if voice_chan_to_rename is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"User {calling_user.mention} needs to be in a Voice Channel to use `~renamevc`!",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        try:
            oldvcname = voice_chan_to_rename.name
            await voice_chan_to_rename.edit(name=new_name)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
            )
            # reply to user
            await ctx.send(embed=embed)
            return
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Renamed voice channel `{oldvcname}` in category `{voice_chan_to_rename.category}` to {voice_chan_to_rename.mention}",
            inline=False,
        )
        # reply to user
        await ctx.send(embed=embed)

    #####################
    # CATEGORY COMMANDS #
    #####################

    @command_predicates.is_verified()
    @commands.command(
        name="sortcat",
        aliases=["categorysort", "catsort", "sortcategory", "reorderchannels"],
    )
    async def categorysort(self, ctx, cat_name: str = ""):
        """Sort all channels in a category. Specifically for puzzle hunts, `solved-`, `backsolved-`, and `solvedish-`
        prefixes will be put behind channels without a prefix.
        Permission Category : Verified Roles only.

        Usage: `~categorysort`
        """
        logging_utils.log_command("categorysort", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_name == "":
            category_to_sort_name = ctx.channel.category
        else:
            category_to_sort_name = cat_name

        category = await discord_utils.find_category(ctx, category_to_sort_name)

        if category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The category named `{category_to_sort_name}` not found.  Perhaps check your spelling and try again.",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        channel_list = self.sort_channels(category.text_channels)

        start_embed = discord_utils.create_embed()
        start_embed.add_field(
            name=f"Sort Started",
            value=f"Your sort of category `{category.name}` has begun! "
            f"This may take a while. If I run into any errors, I'll let you know.",
        )
        start_embed_msg = await ctx.send(embed=start_embed)

        for idx, channel in enumerate(channel_list):
            # Skip channels already in correct place.
            if channel.position == idx:
                continue
            try:
                await channel.edit(position=idx)
            except nextcord.Forbidden:
                if start_embed_msg:
                    await start_embed_msg.delete()
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"Unable to sort `{channel.mention}`. Do I have the correct `manage_channel` positions?",
                )
                await ctx.send(embed=embed)
                return

        if start_embed_msg:
            await start_embed_msg.delete()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Sorted the channels in `{category.name}`!",
        )
        await ctx.send(embed=embed)

    def sort_channels(
        self,
        channel_list: list,
        prefixes: list = [
            solved_constants.SOLVEDISH_PREFIX,
            solved_constants.BACKSOLVED_PREFIX,
            solved_constants.SOLVED_PREFIX,
        ],
    ) -> list:
        """Sort channels according to some prefixes"""
        channel_list_sorted = sorted(channel_list, key=lambda x: x.name)

        channel_list_prefixes = []
        for prefix in prefixes:
            channel_list_prefixes += list(
                filter(lambda x: x.name.startswith(prefix), channel_list_sorted)
            )

        unsolved = channel_list_sorted
        unsolved = list(filter(lambda x: x not in channel_list_prefixes, unsolved))

        return unsolved + channel_list_prefixes

    @command_predicates.is_verified()
    @commands.command(name="renamecat", aliases=["renamecategory"])
    async def renamecategory(self, ctx, cat_a_name: str, cat_b_name: str = ""):
        """Renames the given category to whatever is asked

        Note that if you use more than 2 category renaming commands quickly, Discord automatically stops any more channel-name changes for 10 more minutes.
        Those categories will have to be renamed manually, or wait for the full 10 mins.

        Permission Category : Verified Roles only.
        Usage: `~renamecat newname` (Changes current category name to newname)
        Usage: `~renamecat "CatA" CatB` (Changes CatA name to CatB)
        """
        # log command in console
        logging_utils.log_command("renamecategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_b_name == "":
            old_category_name = ctx.channel.category.name
            new_category_name = cat_a_name
        else:
            old_category_name = cat_a_name
            new_category_name = cat_b_name

        old_category = await discord_utils.find_category(ctx, old_category_name)

        if old_category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The category named `{old_category_name}` not found.  Perhaps check your spelling and try again.",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        try:
            # rename category
            await old_category.edit(name=new_category_name)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the `manage_channels` permisisons?",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Renamed `{old_category_name}` to `{new_category_name}`!",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(name="synccat", aliases=["synccategory", "catsync"])
    async def synccategory(self, ctx, cat_name: str = ""):
        """Changes permissions of all channels in Current Category to be synced to Cat-permissions.
        So any channel with different role permissions set up is reverted.

        Permission Category : Trusted Roles only.
        Usage: `~synccat` (Syncs current category)
        Usage: `~synccat "CatA"` (Syncs given category)
        """
        logging_utils.log_command("synccategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_name == "":
            category_to_sync_name = ctx.channel.category
        else:
            category_to_sync_name = cat_name

        category = await discord_utils.find_category(ctx, category_to_sync_name)

        if category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The category named `{category_to_sync_name}` not found.  Perhaps check your spelling and try again.",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        start_embed = discord_utils.create_embed()
        start_embed.add_field(
            name="Sync Started",
            value=f"Your syncing of category `{category.name}`"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )
        start_msg = await ctx.send(embed=start_embed)

        try:
            for channel in category.channels:
                await channel.edit(sync_permissions=True)
        except nextcord.Forbidden:
            if start_msg:
                await start_msg.delete()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Forbidden! Have you checked if the bot has the required permisisons?",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        if start_msg:
            await start_msg.delete()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"All channels in category `{category.name}` successfully synced to Category!",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="shiftcat", aliases=["shiftcategory", "movecategory", "movecat"]
    )
    async def shiftcategory(self, ctx, cat_a_name: str, cat_b_name: str = ""):
        """Shifts a category to below another category.

        Note : Use "0" or "top" instead to say "Top of the server". But if a category in the server is named "top" or "0" then the respective argument wont work

        Permission Category : Verified Roles only.
        Usage: `~shiftcat "Category A" "Category B"` (Shifts Cat A to just below Cat B)
        Usage: `~shiftcat "Category B"` (Shifts the current category to just below Category B)
        Usage: `~shiftcat "Category A" 0` (Shifts Cat A to the top)
        Usage: `~shiftcat top` (Shifts the current category to the top)
        """
        logging_utils.log_command("shiftcategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        pos_to_shift_to = -1
        cat_to_shift_name = None

        if cat_b_name == "" and cat_a_name in ["top", "0"]:
            # Shift Currcat to top
            cat_to_shift_name = ctx.channel.category
            pos_to_shift_to = 0
        elif cat_b_name in ["top", "0"]:
            # Shift cat A to top
            cat_to_shift_name = cat_a_name
            pos_to_shift_to = 0
        else:
            if cat_b_name == "":
                # Shift Currcat to catA
                cat_to_shift_name = ctx.channel.category
                cat_shifting_to_name = cat_a_name
            else:
                # Shift catA to catB
                cat_to_shift_name = cat_a_name
                cat_shifting_to_name = cat_b_name

        if cat_to_shift_name is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The current channel {ctx.channel.mention} does not exist in a category I can move. Check `~help shiftcat`.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        cat_to_shift = await discord_utils.find_category(ctx, cat_to_shift_name)
        if cat_to_shift is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I cannot find category `{cat_to_shift_name}`. Perhaps check your spelling and try again.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        # Not top, so position needs to be given
        if pos_to_shift_to == -1:
            cat_shifting_to = await discord_utils.find_category(
                ctx, cat_shifting_to_name
            )
            if cat_shifting_to is None:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I cannot find category `{cat_shifting_to_name}`. Perhaps check your spelling and try again.",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return
            pos_to_shift_to = cat_shifting_to.position + 1

        try:
            await cat_to_shift.edit(position=pos_to_shift_to)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I was unable to shift category `{cat_to_shift}`. Do I have the `manage_channels` permission?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if pos_to_shift_to == 0:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Succesfully moved Category `{cat_to_shift}` to top of the server.",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Succesfully moved Category `{cat_to_shift}` to just below Category `{cat_shifting_to}`",
                inline=False,
            )
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(
        name="clonecat",
        aliases=["copycategory", "clonecategory", "copycat", "catclone"],
    )
    async def clonecategory(
        self,
        ctx,
        origCatName: str,
        targetCatName: str,
        origRole: Union[nextcord.Role, str] = None,
        targetRole: Union[nextcord.Role, str] = None,
    ):
        """Clones one category as another.
        If roles are given, takes OrigRole's perms in OrigCat and clones them for Targetrole in TargetCat.
        Creates targetCat if it doesn't exist already.
        Create targetRole if it doesn't exist already (with same server permissions). See `~clonerole` for example.

        Permission Category : Verified Roles only.
        Usage: `~clonecategory "Category A" "Category B"` (Clones Cat A as Cat B)
        Usage: `~clonecategory "Category A" "Category B" @RoleC @RoleD` (Clones Cat A as Cat B. Takes RoleC permission on Cat A, and replicates it with RoleD and Cat B)
        """
        logging_utils.log_command("clonecategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        # Input parsing I guess
        # First, make sure origCat exists
        origCat = await discord_utils.find_category(ctx, origCatName)
        if origCat is None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I cannot find category {origCatName}. Perhaps check your spelling and try again.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return
        # Either neither origRole nor targetRole are supplied, or both are. If XOR, that's a fail.
        if (
            origRole is not None
            and targetRole is None
            or origRole is None
            and targetRole is not None
        ):
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Next time, please supply both `origRole` and `targetRole`, or neither.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        origRole_or_none = await discord_utils.find_role(ctx, origRole)
        targetRole_or_none = await discord_utils.find_role(ctx, targetRole)

        # If we have looped over all the roles and still can't find an origRole, then that's an error
        if origRole_or_none is None and origRole is not None:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Cannot find role {origRole}, are you sure it exists? Retry this command with @{origRole} "
                + f"if it does.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        # if targetRole doesn't exist, create it
        if targetRole_or_none is None and targetRole is not None:
            try:
                targetRole = await ctx.guild.create_role(
                    name=targetRole,
                    permissions=origRole_or_none.permissions,
                    colour=origRole_or_none.colour,
                    hoist=origRole_or_none.hoist,
                    mentionable=origRole_or_none.mentionable,
                )
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"\nCreated {targetRole.mention} with the same server permissions as {origRole_or_none.mention}",
                    inline=False,
                )
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"I was unable to create role {targetRole}. Do I have the `manage_roles` permission?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

        targetCat = await discord_utils.find_category(ctx, targetCatName)
        try:
            # if targetCat doesn't exist, create it
            if targetCat is None:
                targetCat = await origCat.clone(name=targetCatName)
                await targetCat.edit(position=origCat.position + 1)
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"Cloned `{origCat}` as `{targetCat}`",
                    inline=False,
                )
            # if targetCat exists, but no roles were given
            elif origRole is None:
                embed.add_field(
                    name=f"{constants.SUCCESS}",
                    value=f"Nothing to do. Category `{origCat}` and `{targetCat}` already exist, and no roles were given to sync.",
                    inline=False,
                )

            if origRole is not None:
                if origRole in origCat.overwrites:
                    await targetCat.set_permissions(
                        targetRole, overwrite=origCat.overwrites[origRole]
                    )
                    # await targetCat.set_permissions(origRole, overwrite=None)
                    embed.add_field(
                        name=f"{constants.SUCCESS}",
                        value=f"Synced {targetRole.mention}'s permissions in `{targetCat}` with {origRole.mention}'s in `{origCat}`",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name=f"{constants.FAILED}",
                        value=f"{origRole.mention} does not seem to have permission overwrites in `{origCat}`",
                        inline=False,
                    )
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I was unable to create category {targetCatName}. Do I have the `manage_channels` permission?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="listcat",
        aliases=["lscategories", "listcats", "lscats", "listcategories", "lscat"],
    )
    async def listcategories(self, ctx, cat_name: str = ""):
        """List all the categories in a server. If Category is provided, list all channels in it.

        Permission Category : Admin and Bot Owner only.
        Usage: `~listcat` (List all the categories in the server)
        Usage: `~listcat "Cat A"` (List all the channels in the given category)
        """
        logging_utils.log_command("listcategories", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_name == "":
            # Return all category names in the server
            categories = [
                f"{cat.name}         : {len(cat.channels)}"
                for cat in ctx.guild.categories
            ]
            embed.add_field(
                name=f"Categories in {ctx.guild.name}",
                value=f"{chr(10).join(categories)}",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        # Return the channel names in a given category
        category = await discord_utils.find_category(ctx, cat_name)

        if category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The category named `{cat_name}` not found.  Perhaps check your spelling and try again.",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        channel_list = category.channels
        channels = [f"{chan.mention}" for chan in channel_list]
        if channels == []:
            channels = ["(This Category is empty)"]
        embed.add_field(
            name=f"Channels in {category}",
            value=f"{chr(10).join(channels)}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="deletecat",
        aliases=[
            "delcategory",
            "delcat",
            "deletecategory",
            "removecat",
            "removecategory",
            "rmcat",
            "rmcategory",
        ],
    )
    @command_predicates.is_guild_owner()
    async def deletecategory(self, ctx, cat_name: str = ""):
        """Delete a category in the server. Requires emoji confirmation

        Permission Category : Server Owner only.
        Usage: `~deletecat "Cat A"` (List all the channels in the given category)
        """
        logging_utils.log_command("deletecategory", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if cat_name == "":
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"No category given",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        # Return the channel names in a given category
        category = await discord_utils.find_category(ctx, cat_name)

        if category is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Error! The category named `{cat_name}` not found.  Perhaps check your spelling and try again.",
                inline=False,
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        channel_list = category.channels

        channels = [f"#{chan.name}" for chan in channel_list]
        if channels == []:
            channels = ["(This Category is empty)"]

        confirm_emoji = "✅"
        cancel_emoji = "❌"

        # Send warning to user
        embed.add_field(
            name="Are you sure?",
            value=f"This will delete the category `{category.name}` and all its channels. This is not reversable. Make sure you archive the category first before continuing. You have 15 seconds to confirm.",
        )
        embed.add_field(
            name=f"Channels to delete", value=f"{chr(10).join(channels)}", inline=False
        )

        embeds = discord_utils.split_embed(embed)
        for e in embeds:
            emb = await ctx.send(embed=e)

        await emb.add_reaction(confirm_emoji)
        await emb.add_reaction(cancel_emoji)

        # check that the reaction is the correct one and that the correct user reacted
        def chk(reaction, user):
            return (
                reaction.message.id == emb.id
                and (reaction.emoji == confirm_emoji or reaction.emoji == cancel_emoji)
                and user == ctx.author
            )

        final_embed = discord_utils.create_embed()

        try:
            react, _ = await self.bot.wait_for(
                event="reaction_add", check=chk, timeout=15
            )
            # delete category
            if react.emoji == confirm_emoji:
                try:
                    for channel in channel_list:
                        await channel.delete()
                    await category.delete()
                    final_embed.add_field(
                        name=f"{constants.SUCCESS}!",
                        value=f"The category named `{category.name}` has been deleted!",
                        inline=False,
                    )
                    final_embed.add_field(
                        name=f"Channels deleted",
                        value=f"{chr(10).join(channels)}",
                        inline=False,
                    )
                except:
                    final_embed.add_field(
                        name=f"{constants.FAILED}!",
                        value=f"The category named `{category.name}` could not be deleted!",
                        inline=False,
                    )
            else:
                final_embed.add_field(
                    name="Canceled",
                    value="The operation was cancelled.",
                    inline=False,
                )
        except asyncio.TimeoutError:
            final_embed.add_field(name="Canceled", value="The operation was cancelled.")
        finally:
            embeds = discord_utils.split_embed(final_embed)
            for e in embeds:
                await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(ChannelManagementCog(bot))
