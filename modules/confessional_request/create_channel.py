from typing import Optional

import nextcord
from nextcord.ext import commands


class CreateChannelButton(nextcord.ui.Button["CreateChannelView"]):
    def __init__(self, label: str, title_suffix: str):
        self._title_suffix = title_suffix
        super().__init__(label=label, custom_id=f"ticket:create")

    async def callback(self, interaction: nextcord.Interaction):
        """Callback for the button. Creates a new channel in the category for the user"""
        assert (
            interaction.guild is not None
            and interaction.message is not None
            and isinstance(interaction.user, nextcord.Member)
            and len(interaction.message.embeds) > 0
            and isinstance(interaction.message.embeds[0].title, str)
        )
        # defer so we can take some time to create the channel
        await interaction.response.defer()
        # get the category
        embed_title = interaction.message.embeds[0].title
        category_name = embed_title.removesuffix(self._title_suffix)
        category = nextcord.utils.find(
            lambda c: c.name == category_name, interaction.guild.categories
        )
        if category is None:
            return await interaction.send(
                f"Could not find the category {category_name}. Please contact an administrator.",
                ephemeral=True,
            )
        # check if the user already has a channel
        user_mention = interaction.user.mention
        channel = nextcord.utils.find(
            lambda c: c.topic == user_mention, category.text_channels
        )
        if channel is not None:
            embed = nextcord.Embed(
                title="You already have a channel!",
                description=f"You can view your channel here: {channel.mention}",
                color=nextcord.Colour.red(),
            )
            return await interaction.send(embed=embed, ephemeral=True)
        # create the channel
        channel = await category.create_text_channel(
            f"{interaction.user.name}",
            reason=f"{interaction.user.name} requested a channel",
            topic=interaction.user.mention,
        )
        # give the user manage messages permission on the channel
        await channel.set_permissions(interaction.user, manage_messages=True)
        # send a message to the channel
        embed = nextcord.Embed(
            description=f"""Welcome to your private confessional channel where spectators and dead players can read your thoughts! You can say anything here regarding the game you are playing in!

Please note that this channel can be seen by the players of the other game, so you may not talk about any aspects of the other game in here, and you may lose spectating permissions or face removal from the game if you break the rules.

If you have a question, please ping <@981849279897428048>!""",
            color=0x009999,
        )
        embed.set_author(
            name=f"{interaction.user.name}",
            icon_url=interaction.user.display_avatar.url,
        )
        await channel.send(
            content=f"{interaction.user.mention} has created a confessional channel!",
            embed=embed,
        )
        # respond to the button interaction
        embed = nextcord.Embed(
            title="Your channel has been created",
            description=f"You can now write confessionals in {channel.mention}",
            color=0x009999,
        )
        await interaction.send(embed=embed, ephemeral=True)


class CreateChannelView(nextcord.ui.View):
    def __init__(
        self,
        label: str,
        title_suffix: str,
        ctx: Optional[commands.Context] = None,
    ):
        """View for the create channel button

        Arguments:
            label (str): The label of the button
            title_suffix (str): The suffix to append to the title.
            ctx (Optional[commands.Context]): The context of the command.
                This does not need to be supplied when adding this as a persistent view.
        """
        super().__init__(timeout=None)
        self._ctx = ctx
        self._button = CreateChannelButton(label=label, title_suffix=title_suffix)
        self.add_item(self._button)
