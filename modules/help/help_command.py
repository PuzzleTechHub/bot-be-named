import os
import re

import nextcord
from nextcord.ext import commands
import database
from utils import discord_utils

# Commands shown on each page of a module's help.
COMMANDS_PER_PAGE = 10
# Seconds without a button press before the menu stops responding.
MENU_TIMEOUT = 120
# Max amount of options in a dropdown menu (enforced by Discord)
MAX_SELECT_OPTIONS = 25
# Max length of an embed field's value (enforced by Discord)
MAX_FIELD_VALUE = 1024


def unwrap(text: str) -> str:
    """Joins a docstring's wrapped sentences back together. A line starting with a lowercase
    letter carries on the sentence above it. Other line breaks, like separate Usage lines, stay."""
    return re.sub(r"[ \t]*\n[ \t]*(?=[a-z])", " ", text)


def command_summary(command: commands.Command) -> str:
    """The command's brief, or else the whole first paragraph of its docstring on one line.
    nextcord's short_doc stops at the first line break, which cuts wrapped sentences short."""
    if command.brief:
        return command.brief
    paragraph = " ".join((command.help or "").split("\n\n", 1)[0].split())
    if len(paragraph) > MAX_FIELD_VALUE:
        paragraph = paragraph[: MAX_FIELD_VALUE - 1] + "…"
    return paragraph or "..."


class HelpMenu(nextcord.ui.View):
    """Public help message with a module dropdown and previous/next buttons. Only the person who
    called the command can use the controls."""

    def __init__(self, author_id: int, pages: list, start: int = 0):
        """pages is a list of (module name, or None for the overview, embed)."""
        super().__init__(timeout=MENU_TIMEOUT)
        self.author_id = author_id
        self.pages = pages
        self.index = start
        self.message = None

        options = [nextcord.SelectOption(label="Overview", value="Overview")]
        for name in dict.fromkeys(name for name, _ in pages if name is not None):
            options.append(nextcord.SelectOption(label=name[:100], value=name[:100]))
        # Discord needs a dropdown with a custom_id, so make a random one for it
        self.module_select = nextcord.ui.StringSelect(
            custom_id=os.urandom(16).hex(),
            placeholder="Jump to a module",
            options=options[:MAX_SELECT_OPTIONS],
            row=0,
        )
        self.module_select.callback = self.select_module
        self.add_item(self.module_select)

        self.previous_button = nextcord.ui.Button(emoji="◀", row=1)
        self.previous_button.callback = self.previous_page
        self.add_item(self.previous_button)
        self.next_button = nextcord.ui.Button(emoji="▶", row=1)
        self.next_button.callback = self.next_page
        self.add_item(self.next_button)
        self._update_buttons()

    @property
    def embed(self) -> nextcord.Embed:
        return self.pages[self.index][1]

    def _update_buttons(self):
        self.previous_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.pages) - 1

    async def _show(self, interaction: nextcord.Interaction, index: int):
        self.index = max(0, min(index, len(self.pages) - 1))
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def previous_page(self, interaction: nextcord.Interaction):
        await self._show(interaction, self.index - 1)

    async def next_page(self, interaction: nextcord.Interaction):
        await self._show(interaction, self.index + 1)

    async def select_module(self, interaction: nextcord.Interaction):
        chosen = self.module_select.values[0]
        for index, (name, _) in enumerate(self.pages):
            if (name or "Overview")[:100] == chosen:
                await self._show(interaction, index)
                return

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if interaction.user is not None and interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "Only the person who ran this help command can use these buttons. "
            "Run the help command yourself to get your own menu.",
            ephemeral=True,
        )
        return False

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except nextcord.HTTPException:
                pass  # The message was deleted, so there is nothing to update.


class HelpCommand(commands.MinimalHelpCommand):
    """Custom help command override using embeds"""

    def get_ending_note(self):
        """Returns note to display at the bottom"""
        prefix = self.context.clean_prefix
        invoked_with = self.invoked_with
        return f"Use {prefix}{invoked_with} [command] for more info on a command."

    def get_command_signature(self, command: commands.core.Command):
        """Retrieves the signature portion of the help page."""
        return f"{command.qualified_name} {command.signature}"

    def command_not_found(self, string):
        """Intercept ~help a_custom_command errors"""
        command_name = string.lower()

        if self.context.guild and command_name in database.CUSTOM_COMMANDS.get(
            self.context.guild.id, {}
        ):
            # Return special marker that we'll catch in send_error_message
            return f"__CUSTOM_COMMAND__{command_name}"

        return f"No command called '{string}' found."
        # TODO global custom commands

    async def send_error_message(self, error):
        """Override to send custom command info as embed"""
        if error.startswith("__CUSTOM_COMMAND__"):
            command_name = error.replace("__CUSTOM_COMMAND__", "")
            embed = discord_utils.create_embed()
            embed.add_field(
                name="That's a custom command!",
                value=f'The command "{command_name}" is a custom command created for this server!\n\n'
                f"Use `~help Custom Commands` to see how they work!\n\n"
                f"Your custom command response is: {database.CUSTOM_COMMANDS[self.context.guild.id][command_name]}",
                inline=False,
            )
            await self.get_destination().send(embed=embed)
        else:
            # Send regular error message
            embed = discord_utils.create_embed()
            embed.description = error
            await self.get_destination().send(embed=embed)

    async def bot_help_embed(self, mapping: dict) -> nextcord.Embed:
        """The overview page with every module and what it is for. The commands are on each
        module's own page."""
        prefix = self.context.clean_prefix
        embed = discord_utils.create_embed()
        embed.title = "Bot Commands"
        embed.set_author(
            name=self.context.bot.user.name,
            icon_url=self.context.bot.user.display_avatar.url,
        )
        description = self.context.bot.description or ""
        embed.description = (
            f"{description}\n\n" if description else ""
        ) + f"Pick a module below, or use `{prefix}help [module]`, to see its commands."

        for cog in sorted(
            (cog for cog in mapping if cog is not None),
            key=lambda cog: cog.qualified_name,
        ):
            # Only list modules the caller has a command they can use in
            if await self.filter_commands(mapping[cog]):
                embed.add_field(name=cog.qualified_name, value=cog.description or "...")

        embed.set_footer(text=self.get_ending_note())
        return embed

    async def cog_help_embeds(self, cog: commands.Cog) -> list:
        """A module's commands, COMMANDS_PER_PAGE to an embed.
        Empty if the caller can't use any of them."""
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        chunks = [
            filtered[start : start + COMMANDS_PER_PAGE]
            for start in range(0, len(filtered), COMMANDS_PER_PAGE)
        ]
        embeds = []
        for number, chunk in enumerate(chunks, start=1):
            embed = discord_utils.create_embed()
            embed.title = f"{cog.qualified_name} Commands"
            if len(chunks) > 1:
                embed.title += f" ({number}/{len(chunks)})"
            if cog.description:
                embed.description = cog.description
            for command in chunk:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command_summary(command),
                    inline=False,
                )
            embed.set_footer(text=self.get_ending_note())
            embeds.append(embed)
        return embeds

    async def help_pages(self) -> list:
        """The overview, then each module in name order."""
        mapping = self.get_bot_mapping()
        pages = [(None, await self.bot_help_embed(mapping))]
        for cog in sorted(
            (cog for cog in mapping if cog is not None),
            key=lambda cog: cog.qualified_name,
        ):
            for embed in await self.cog_help_embeds(cog):
                pages.append((cog.qualified_name, embed))
        return pages

    async def send_menu(self, pages: list, start: int = 0):
        """Send pages as one public message with a HelpMenu, showing pages[start]."""
        for number, (_, embed) in enumerate(pages, start=1):
            embed.set_footer(
                text=f"Page {number}/{len(pages)} • {self.get_ending_note()}"
            )
        view = HelpMenu(self.context.author.id, pages, start)
        view.message = await self.get_destination().send(embed=view.embed, view=view)

    async def send_bot_help(self, mapping: dict):
        """implements bot command help page"""
        await self.send_menu(await self.help_pages())

    async def send_cog_help(self, cog: commands.Cog):
        """implements cog help page, as the menu opened at that module"""
        pages = await self.help_pages()
        for index, (name, _) in enumerate(pages):
            if name == cog.qualified_name:
                await self.send_menu(pages, start=index)
                return
        embed = discord_utils.create_embed()
        embed.title = f"{cog.qualified_name} Commands"
        embed.description = "You can't use any of the commands in this module here."
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        """implements group help page and command help page"""
        prefix = self.context.clean_prefix
        embed = discord_utils.create_embed()
        embed.title = group.qualified_name
        if group.help:
            embed.description = unwrap(group.help)

        if group.cog is not None:
            embed.add_field(name="Module", value=group.cog.qualified_name)
        if group.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"{prefix}{alias}" for alias in group.aliases),
            )
        # Most docstrings already give usage examples, which are clearer than the signature
        if "Usage:" not in (group.help or ""):
            embed.add_field(
                name="Usage",
                value=f"`{prefix}{self.get_command_signature(group).strip()}`",
                inline=False,
            )

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command_summary(command),
                    inline=False,
                )

        await self.get_destination().send(embed=embed)

    # Use the same function as group help for command help
    send_command_help = send_group_help
