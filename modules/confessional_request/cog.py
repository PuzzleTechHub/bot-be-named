import asyncio
import copy

import nextcord
from nextcord.ext import commands

import constants
from utils import discord_utils, logging_utils

from .create_channel import CreateChannelView
from .select_category import SelectCategoryView


class ConfessionalRequest(commands.Cog, name="Confessional Request"):
    """Channel request button system"""

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._persistent_view_added = False
        self.BUTTON_TEXT = "Create Confessional Channel"
        self.EMBED_TITLE_SUFFIX = " Channel Request"

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._persistent_view_added:
            self._persistent_view_added = True
            button_view = CreateChannelView(self.BUTTON_TEXT, self.EMBED_TITLE_SUFFIX)
            self._bot.add_view(button_view)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketbtn(self, ctx: commands.Context):
        """Creates a button for creating a confessional channel"""
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server")
        logging_utils.log_command("ticketbtn", ctx.guild, ctx.channel, ctx.author)
        # prompt for a category
        category_view = SelectCategoryView(categories=ctx.guild.categories, ctx=ctx)
        category_msg = await ctx.reply(f"Please select a category", view=category_view)
        await category_view.wait()
        category = category_view.dropdown.selected_category
        await category_msg.delete()
        if category is None:
            return await ctx.send("No category selected", delete_after=3)
        # create the button view
        button_view = CreateChannelView(
            label=self.BUTTON_TEXT,
            title_suffix=self.EMBED_TITLE_SUFFIX,
            ctx=ctx,
        )
        embed = nextcord.Embed(
            title=f"{category.name}{self.EMBED_TITLE_SUFFIX}",
            description=f'If you want to write confessionals in {category.name}, click "{self.BUTTON_TEXT}" below. This will make a private confessional channel for you where spectators and dead players can read your thoughts!',
            color=0x009999,
        )
        await ctx.send(embed=embed, view=button_view)
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def close(self, ctx: commands.Context):
        """Archives and closes the channel that the user is currently in"""
        # check that the topic is a user mention
        logging_utils.log_command("close", ctx.guild, ctx.channel, ctx.author)
        ticket_channel = ctx.channel
        if not getattr(ticket_channel, "topic", "").startswith("<@"):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="You are not in a confessional channel",
            )
            return await ctx.send(embed=embed)
        assert ctx.guild is not None
        assert isinstance(ticket_channel, nextcord.TextChannel)
        archivechannel_cmd = self._bot.get_command("archivechannel")
        assert isinstance(archivechannel_cmd, commands.Command)
        archives_channel = nextcord.utils.find(
            lambda c: c.name == f"channel-archives", ctx.guild.text_channels
        )
        if archives_channel is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="#channel-archives channel was not found",
            )
            return await ctx.send(embed=embed)
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Archiving in progress", value=f"This may take a while.")
        progress_msg = await ctx.send(embed=embed)
        # create a context where the message is the last message in the archive channel
        fake_ctx = copy.copy(ctx)
        fake_ctx.channel = archives_channel  # type: ignore
        # execute "~archivechannel #<ticket-channel>"
        await archivechannel_cmd(fake_ctx, ticket_channel)
        # check that the new last message contains the attachment
        last_message = None
        if archives_channel.last_message is not None:
            last_message = archives_channel.last_message
        if last_message is None and archives_channel.last_message_id is not None:
            last_message = await archives_channel.fetch_message(archives_channel.last_message_id)
        if last_message and last_message.attachments and not last_message.embeds:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value=f"The channel has been archived and will now be deleted.",
            )
            await progress_msg.edit(embed=embed)
            await asyncio.sleep(2)
            await ticket_channel.delete()
        else:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The channel was not archived properly. See {archives_channel.mention} for more information.",
            )
            await progress_msg.edit(embed=embed)
            await ctx.send(
                f"{ticket_channel.topic}, this channel may have too many attachments."
                "Please save your attachments so this channel can be archived and deleted."
            )


def setup(bot: commands.Bot):
    bot.add_cog(ConfessionalRequest(bot))
