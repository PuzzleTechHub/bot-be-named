"""
Button pager for multi-page embeds (e.g. ~help and Nutrimatic results).
"""

import contextlib

import nextcord
from nextcord.ext import commands

# Seconds without a button press before the buttons stop responding.
PAGE_TIMEOUT = 120


class PageView(nextcord.ui.View):
    """Previous/next buttons that step through a list of embeds on one message. Only the
    person who ran the command can press them, and they are disabled after the timeout."""

    not_owner_message = (
        "Only the person who ran this command can use these buttons. "
        "Run the command yourself to get your own."
    )

    def __init__(
        self,
        author_id: int,
        embeds: list[nextcord.Embed],
        start: int = 0,
        timeout: float = PAGE_TIMEOUT,
        button_row: int = 0,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.embeds = embeds
        self.index = max(0, min(start, len(embeds) - 1))
        self.message = None

        self.previous_button = nextcord.ui.Button(emoji="◀", row=button_row)
        self.previous_button.callback = self.previous_page
        self.add_item(self.previous_button)
        self.next_button = nextcord.ui.Button(emoji="▶", row=button_row)
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)
        self._update_buttons()

    @property
    def embed(self) -> nextcord.Embed:
        return self.embeds[self.index]

    def _update_buttons(self):
        self.previous_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.embeds) - 1

    async def _show(self, interaction: nextcord.Interaction, index: int):
        self.index = max(0, min(index, len(self.embeds) - 1))
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def previous_page(self, interaction: nextcord.Interaction):
        await self._show(interaction, self.index - 1)

    async def next_page(self, interaction: nextcord.Interaction):
        await self._show(interaction, self.index + 1)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user is not None and interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(self.not_owner_message, ephemeral=True)
        return False

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            # The message may have been deleted, then there is nothing to update
            with contextlib.suppress(nextcord.HTTPException):
                await self.message.edit(view=self)


async def send_pages(ctx: commands.Context, embeds: list[nextcord.Embed]):
    """Send embeds as one message, with buttons when there is more than one page."""
    if len(embeds) == 1:
        return await ctx.send(embed=embeds[0])
    view = PageView(ctx.author.id, embeds)
    view.message = await ctx.send(embed=view.embed, view=view)
    return view.message
