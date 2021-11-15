import typing
import discord
from discord.ext import commands
import aiohttp
import io
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS

import constants
from utils import discord_utils, logging_utils, command_predicates


class DiscordCog(commands.Cog, name="Discord"):
    """Discord Utility Commands"""

    def __init__(self, bot):
        self.bot = bot

    ####################
    # PINNING COMMANDS #
    ####################

    @command_predicates.is_verified()
    @commands.command(name="pin")
    async def pin(self, ctx):
        """Pin a message (Either reply to the message, or it auto pins the message above)

        Category : Verified Roles only.
        Usage: `~pin` (as reply to message)
        Usage: `~pin` (to just pin the last message)
        """
        logging_utils.log_command("pin", ctx.guild, ctx.channel, ctx.author)

        pins = await ctx.message.channel.pins()
        if(len(pins)==50):
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"This channel already has max. number of pins (50)!",
                            inline=False)
            await ctx.send(embed=embed)
            return 0

        if not ctx.message.reference:
            channel_history = await ctx.message.channel.history(limit=2).flatten()
            msg = channel_history[-1]
        else:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
        try:
            await msg.unpin()
            x = await msg.pin()
            channel_history = await ctx.message.channel.history(limit=5).flatten()
            for pinmsg in channel_history:
                if pinmsg.is_system():
                    await pinmsg.delete()
                    break
            await ctx.message.add_reaction(EMOJIS[':white_check_mark:'])
        except discord.HTTPException:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"Cannot pin system messages (e.g. **{self.bot.user.name}** pinned **a message** to this channel.)",
                            inline=False)
            await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="pinme")
    async def pinme(self, ctx):
        """Pins the message that called it.

        Category : Verified Roles only.
        Usage : `~pinme Message`
        """
        logging_utils.log_command("pinme", ctx.guild, ctx.channel, ctx.author)

        pins = await ctx.message.channel.pins()
        if(len(pins)==50):
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"This channel already has max. number of pins (50)!",
                            inline=False)
            await ctx.send(embed=embed)
            return 0

        try:
            await ctx.message.pin()
        except discord.HTTPException:
            embed = discord_utils.create_embed()
            embed.add_field(name="Error!",
                            value=f"Issue pinning message. Perhaps I don't have permissions to pin?",
                            inline=False)
            await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="lspin", aliases=["lspins", "listpin", "listpins"])
    async def listpin(self, ctx):
        """Lists all the pinned posts in the current channel

        Category : Verified Roles only.
        Usage: `~listpins~`"""
        logging_utils.log_command("listpin", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        pins = await ctx.message.channel.pins()

        if len(pins) == 0:
            embed.add_field(name="Success!",
                            value="There are 0 pinned posts on this channel.",
                            inline=False)
            await ctx.send(embed=embed)
            return 1
        
        strmsg = ""
        i=1
        for pin in pins:
            strmsg = strmsg + f"[Msg{i}]({pin.jump_url}) : "
            i=i+1
        
        embed.add_field(name="Success!",
                        value=f"There are {len(pins)} pinned posts on this channel." 
                            f"\n{strmsg[:-3]}",
                        inline=False)
        embeds = discord_utils.split_embed(embed)
        for embed in embeds:
            await ctx.send(embed=embed)
    
    @command_predicates.is_verified()
    @commands.command(name="unpin")
    async def unpin(self, ctx, num_to_unpin: int = 1):
        """Unpins a specific message from a channel, or a given number of pins

        Category : Verified Roles only.
        Usage: `~unpin 2` (unpins latest 2 pins)
        Usage: (as a reply to pinned message) `~unpin`
        """
        logging_utils.log_command("unpin", ctx.guild, ctx.channel, ctx.author)
        if num_to_unpin < 1 or not isinstance(num_to_unpin, int):
            embed = discord_utils.create_no_argument_embed("number of messages to unpin")
            await ctx.send(embed=embed)
            return

        embed = discord_utils.create_embed()
        pins = await ctx.message.channel.pins()
        messages_to_unpin = []
        strmsg = ""

        reply = False
        #If unpin is in direct reply to another message, unpin only that message
        if ctx.message.reference:
            reply = True
            orig_msg = ctx.message.reference.resolved
            #TODO - if orig_msg is DeletedReferencedMessage
            if not orig_msg.pinned:
                embed.add_field(name="Error!",
                                value=f"The linked message [Msg]({orig_msg.jump_url}) has not been pinned, there's nothing to unpin.",
                                inline=False)
                await ctx.send(embed=embed)
                return
            messages_to_unpin.append(orig_msg)
        #Else unpin the last X messages
        else:
            if num_to_unpin < len(pins):
                messages_to_unpin = pins[:num_to_unpin]
            #If too many messages to unpin, just unpin all
            else:
                messages_to_unpin = pins

        i=1
        for pin in messages_to_unpin:
            try:
                await pin.unpin()
                strmsg = strmsg + f"[Msg{i}]({pin.jump_url}) : "
                i=i+1
            except discord.HTTPException:
                embed.add_field(name="Error!",
                                value=f"I do not have permissions to unpin that message "
                                      f"(or some other error, but probably perms)",
                                inline=False)
                await ctx.send(embed=embed)
                return

        embed.add_field(name="Success!",
                        value=f"Unpinned {'the most recent' if not reply else ''} {num_to_unpin} {'messages' if num_to_unpin != 1 else 'message'}\n" + 
                            f"{strmsg[:-3]}",
                        inline=False)
        await ctx.send(embed=embed)

    #######################
    # STATISTICS COMMANDS #
    #######################

    @commands.command(name="stats")
    async def stats(self, ctx):
        """Get server stats

        Usage: `~stats`
        """
        logging_utils.log_command("stats", ctx.guild, ctx.channel, ctx.author)
        guild = ctx.guild
        embed = discord_utils.create_embed()
        embed.add_field(name="Members",
                        value=f"{guild.member_count}")
        embed.add_field(name="Roles",
                        value=f"{len(guild.roles)}")
        embed.add_field(name="Emoji (limit)",
                        value=f"{len(guild.emojis)} ({guild.emoji_limit})")
        embed.add_field(name="Categories",
                        value=f"{len(guild.categories)}")
        embed.add_field(name="Text Channels",
                        value=f"{len(guild.text_channels)}")
        embed.add_field(name="Voice Channels",
                        value=f"{len(guild.voice_channels)}")

        await ctx.send(embed=embed)

    @commands.command(name="catstats")
    async def catstats(self, ctx):
        """Get category stats

        Usage: `~catstats`
        """
        logging_utils.log_command("catstats", ctx.guild, ctx.channel, ctx.author)
        cat = ctx.message.channel.category
        embed = discord_utils.create_embed()
        embed.add_field(name="Category Name",
                        value=f"{cat.name}")
        embed.add_field(name="Text Channels",
                        value=f"{len(cat.text_channels)}")
        embed.add_field(name="Voice Channels",
                        value=f"{len(cat.voice_channels)}")
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

    #################
    # ROLE COMMANDS #
    #################

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="assignrole", aliases=["giverole","rolegive","roleassign"])
    async def assignrole(self, ctx, rolename: str, *args):
        """Assign a role to a list of users. If the role does not already exist, then creates the role.
        The role can be mentioned or named. The users must be mentioned.

        Category : Trusted Roles only.        
        Usage: `~assignrole @RoleName @User1 @User2`
        Usage: `~assignrole "NewRoleName" @User1`
        """
        logging_utils.log_command("assignrole", ctx.guild, ctx.channel, ctx.author)
        # User didn't include any people to get the role
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Users to give the role")
            await ctx.send(embed=embed)
            return

        # Get role. Allow people to use the command by pinging the role, or just naming it
        role_to_assign = None
        try:
            # TODO: Fix replace?
            role_to_assign = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        except ValueError:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break

        embed = discord_utils.create_embed()
        # Cannot find the role, so we'll make one
        if not role_to_assign:
            try:
                role_to_assign = await ctx.guild.create_role(name=rolename)
                embed.add_field(name=f"Created role {rolename}",
                                value=f"Could not find role {rolename}, so I created it.",
                                inline=False)
            except discord.Forbidden:
                embed.add_field(name=f"Error!",
                                value=f"I couldn't find role {rolename}, so I tried to make it. But I don't have "
                                      f"permission to add a role in this server. Do I have the `add_roles` permission?",
                                inline=False)
                await ctx.send(embed=embed)
                return

        users_with_role_list = []
        for unclean_username in args:
            # Get the user
            try:
                # TODO: Fix replace?
                user = ctx.guild.get_member(int(unclean_username.replace('<@', '').replace('>', '').replace('!', '')))
                # User not found
                if not user:
                    embed.add_field(name="Error Finding User!",
                                    value=f"Could not find user {unclean_username}. Did you ping them? I won't accept raw usernames",
                                    inline=False)
                    continue
            # User id not provided or bad argument
            except ValueError:
                embed.add_field(name="Error Finding User!",
                                value=f"Could not find user {unclean_username}. Did you ping them? I won't accept raw usernames",
                                inline=False)
                continue
            # Assign the role
            try:
                await user.add_roles(role_to_assign)
                users_with_role_list.append(user)
            except discord.Forbidden:
                embed.add_field(name="Error Assigning Role!",
                                value=f"I could not assign {role_to_assign.mention} to {user}. Either this role is "
                                      f"too high up on the roles list for them, or I do not have permissions to give "
                                      f"them this role. Please ensure I have the `manage_roles` permission.",
                                inline=False)
        if len(users_with_role_list) < 1:
            embed.insert_field_at(0,
                                  name="Failed!",
                                  value=f"Could not assign role {role_to_assign.mention} to anyone.",
                                  inline=False)
        else:
            embed.add_field(name="Success!",
                            value=f"Added the {role_to_assign.mention} role to {', '.join([user.mention for user in users_with_role_list])}",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="createrole", aliases=["makerole"])
    async def createrole(self, ctx, rolename: str, color: str = None, mentionable: bool = True):
        """Create a role in the server. 

        Category : Trusted Roles only.        
        Usage: `~makerole RoleName`
        Usage: `~makerole RoleName d0d0ff True` (colour of role, if the role is mentionable)
        """
        logging_utils.log_command("createrole", ctx.guild, ctx.channel, ctx.author)

        # Convert color from hex str into int
        if color:
            try:
                color = discord.Color(int(color, 16))
            except ValueError:
                embed = discord_utils.create_embed()
                embed.add_field(name=f"Error!",
                                value=f"I didn't understand that color. Make sure you use a valid hex code!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        else:
            color = discord.Color.default()

        try:
            role = await ctx.guild.create_role(name=rolename, color=color, mentionable=mentionable)
        except discord.Forbidden:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error!",
                            value=f"I don't have permission to add a role in this server. Do I have the `add_roles` permission?",
                            inline=False)
            await ctx.send(embed=embed)
            return
        embed = discord_utils.create_embed()
        embed.add_field(name="Success!",
                        value=f"Created role {role.mention}!",
                        inline=False)
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="deleterole", aliases=["removerole", "rmrole"])
    async def deleterole(self, ctx, rolename: str):
        """Remove a role from the server

        Category : Admin or Bot Owner only.
        Usage: `~removerole "RoleName"`
        Usage: `~removerole @RoleMention`
        """
        logging_utils.log_command("deleterole", ctx.guild, ctx.channel, ctx.author)

        embed = discord_utils.create_embed()
        role_to_delete = None
        # Try to find the role if the user mentioned it (e.g. ~deleterole @rolename)
        try:
            # TODO: Fix replace?
            role_to_delete = ctx.guild.get_role(int(rolename.replace('<@&', '').replace('>', '')))
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        except ValueError:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_delete = role
                    break
        # Delete the role or error if it didn't work.
        try:
            if role_to_delete:
                role_name = role_to_delete.name
                await role_to_delete.delete()
                embed.add_field(name="Success!",
                                value=f"Removed role {role_name}",
                                inline=False)
                await ctx.send(embed=embed)
                return
            else:
                embed.add_field(name=f"Error!",
                                value=f"I can't find {rolename} in this server. Make sure you check the spelling and punctuation!",
                                inline=False)
                await ctx.send(embed=embed)
                return
        except discord.Forbidden:
            embed.add_field(name=f"Error!",
                            value=f"I don't have permission to add a role in this server. Do I have the `add_roles` permission?",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="listroles", aliases=["lsroles", "listrole", "lsrole"])
    async def listroles(self, ctx):
        """List all roles in the server

        Usage:`~listroles`
        """
        logging_utils.log_command("listroles", ctx.guild, ctx.channel, ctx.author)
        roles = await ctx.guild.fetch_roles()
        embed = discord.Embed(title=f"Roles in {ctx.guild.name}",
                              description=f"{', '.join([role.mention for role in roles])}",
                              color = constants.EMBED_COLOR)
        await ctx.send(embed=embed)

    ###################
    # BOTSAY COMMANDS #
    ###################

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="botsay")
    async def botsay(self, ctx, channel_id_or_name: str, message_to_say:str):
        """Say something in another channel

        Category : Trusted roles only.
        Usage: `~botsay channelname "Message"`
        Usage: `~botsay #channelmention "Longer Message"`
        """
        logging_utils.log_command("botsay", ctx.guild, ctx.channel, ctx.author)

        embed = discord_utils.create_embed()
        guild = ctx.message.guild

        try:
            channel = discord_utils.find_channel(self.bot, guild.channels, channel_id_or_name)
        except ValueError:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Error! The channel `{channel_id_or_name}` was not found")
            await ctx.send(embed=embed)
            return

        try:
            await channel.send(message_to_say)   
        except discord.Forbidden:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! The bot is unable to speak on {channel.mention}! Have you checked if "
                                  f"the bot has the required permisisons?")
            await ctx.send(embed=embed)
            return

        embed.add_field(name=f"Success!",
                        value=f"Message sent to {channel.mention}: {message_to_say}!")
        # reply to user
        await ctx.send(embed=embed)

    @commands.has_any_role(*constants.TRUSTED)
    @commands.command(name="botsayembed")
    async def botsayembed(self, ctx, channel_id_or_name: str, message_to_say:str):
        """Say something in another channel, but as an embed

        Category : Trusted roles only.
        Usage: `~botsayembed channelname "Message"`
        Usage: `~botsayembed #channelmention "Longer Message"`
        """
        logging_utils.log_command("botsayembed", ctx.guild, ctx.channel, ctx.author)

        guild = ctx.message.guild

        try:
            channel = discord_utils.find_channel(self.bot, guild.channels, channel_id_or_name)
        except ValueError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Error! The channel `{channel_id_or_name}` was not found")
            await ctx.send(embed=embed)
            return

        try:
            sent_embed = discord.Embed(description=message_to_say,
                                  color=constants.EMBED_COLOR)
            await channel.send(embed=sent_embed)
        except discord.Forbidden:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! The bot is unable to speak on {channel.mention}! Have you checked if "
                                  f"the bot has the required permisisons?")
            await ctx.send(embed=embed)
            return

        # reply to user
        sent_embed.add_field(name=f"{constants.SUCCESS}!",
                             value=f"Embed sent to {channel.mention}",
                             inline=False)
        await ctx.send(embed=sent_embed)

    ##################
    # EMOJI COMMANDS #
    ##################

    @command_predicates.is_verified()
    @commands.command(name="listemoji", aliases=["lsemoji","listemojis","lsemojis"])
    async def listemoji(self, ctx):
        """List all emojis in a server

        Category : Verified Roles only.
        Usage: `~listemojis`
        """
        logging_utils.log_command("listemoji", ctx.guild, ctx.channel, ctx.author)
        embed = discord.Embed(title=f"Emoji in {ctx.guild.name}",
                              description=f"{chr(10).join([f'{emoji} {emoji.name} {emoji.id}' for emoji in ctx.guild.emojis])}")
        await ctx.send(embed=embed)

    @command_predicates.is_verified()
    @commands.command(name="steal")
    async def steal(self, ctx, *emojis : typing.Union[discord.Emoji, discord.PartialEmoji]):
        """Steals an emote from another server and uploads it to this server with the same name.
        
        Category : Verified Roles only.
        Usage: `~steal :emote1: :emote2:`
        """
        logging_utils.log_command("steal", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        for emoji in emojis:
            url = str(emoji.url)
            name = emoji.name
            async with aiohttp.ClientSession() as ses:
                async with ses.get(url) as r:
                    try:
                        img_or_gif = io.BytesIO(await r.read())
                        b_value = img_or_gif.getvalue()
                        try:
                            emoji = await ctx.guild.create_custom_emoji(image=b_value, name=name)
                            
                            embed.add_field(name=f"{constants.SUCCESS}",
                                            value=f"Added {emoji} with name {emoji.name}")
                            await ses.close()
                        except discord.Forbidden:
                            embed.add_field(name=f"{constants.FAILED}",
                                            value=f"Error adding `:{name}:` to server. Do I have the correct permissions to manage emotes in this server?")
                            await ses.close()
                        # TODO: What error gets thrown if there are too many emotes?
                        except:                     
                            embed.add_field(name=f"{constants.FAILED}",
                                            value=f"Could not add `:{name}:` to server. Do you have any emote slots left?")
                            await ses.close()
                    except:
                        embed.add_field(name=f"{constants.FAILED}",
                                        value=f"Could not find emote `:{name}:`.")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DiscordCog(bot))
