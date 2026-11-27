import os
import re

import nextcord
from nextcord.ext import commands

import database
from utils import command_predicates, discord_utils, paging_utils

# Commands shown on each page of a module's help.
COMMANDS_PER_PAGE = 10
# Seconds without a button press before the menu stops responding.
MENU_TIMEOUT = 120
# Max amount of options in a dropdown menu (enforced by Discord)
MAX_SELECT_OPTIONS = 25
# Max length of an embed field's value (enforced by Discord)
MAX_FIELD_VALUE = 1024
# Words after ~help that open the commands-by-permission menu
PERMISSION_WORDS = ("permissions", "permission", "perms")
# Each permission category's page title and who it covers, from least to most restricted.
# None is for commands anyone can use. A category missing here goes last, titled by its label.
# {prefix} becomes the server's prefix.
_category = command_predicates.PERMISSION_CATEGORIES
PERMISSION_PAGES = {
    None: ("Everyone", "Anyone can use these."),
    _category["is_solver"]: (
        "Solver Roles",
        "Roles added with `{prefix}addperm Solver @role`.",
    ),
    _category["is_verified"]: (
        "Verified Roles",
        "Roles added with `{prefix}addperm Verified @role`.",
    ),
    _category["is_trusted"]: (
        "Trusted Roles",
        "Roles added with `{prefix}addperm Trusted @role`.",
    ),
    _category["is_trusted_or_bot_owner"]: (
        "Trusted Roles or Bot Owner",
        "Trusted roles, or whoever runs the bot.",
    ),
    _category["is_tester"]: (
        "Tester Roles",
        "Roles added with `{prefix}addperm Tester @role`.",
    ),
    _category["is_admin"]: (
        "Admin",
        "Members with the server's Administrator permission.",
    ),
    _category["is_bot_owner_or_admin"]: (
        "Admin or Bot Owner",
        "Server admins, or whoever runs the bot.",
    ),
    _category["is_bot_owner"]: ("Bot Owner", "Only whoever runs the bot."),
}


def unwrap(text: str) -> str:
    """Joins a docstring's wrapped sentences back together. A line starting with a lowercase
    letter carries on the sentence above it. Other line breaks, like separate Usage lines, stay."""
    return re.sub(r"[ \t]*\n[ \t]*(?=[a-z])", " ", text)


def chunk_names(names: list) -> list:
    """Joins names with commas into as few strings as fit in an embed field."""
    chunks = [""]
    for name in names:
        joined = f"{chunks[-1]}, {name}" if chunks[-1] else name
        if len(joined) > MAX_FIELD_VALUE:
            chunks.append(name)
        else:
            chunks[-1] = joined
    return chunks


def command_summary(command: commands.Command) -> str:
    """The command's brief, or else the whole first paragraph of its docstring on one line.
    nextcord's short_doc stops at the first line break, which cuts wrapped sentences short."""
    if command.brief:
        return command.brief
    paragraph = " ".join((command.help or "").split("\n\n", 1)[0].split())
    if len(paragraph) > MAX_FIELD_VALUE:
        paragraph = paragraph[: MAX_FIELD_VALUE - 1] + "…"
    return paragraph or "..."


class HelpMenu(paging_utils.PageView):
    """Public help message with a module dropdown and previous/next buttons. Only the person who
    called the command can use the controls."""

    not_owner_message = (
        "Only the person who ran this help command can use these buttons. "
        "Run the help command yourself to get your own menu."
    )

    def __init__(
        self,
        author_id: int,
        pages: list,
        start: int = 0,
        placeholder: str = "Jump to a module",
    ):
        """pages is a list of (module name, or None for the overview, embed)."""
        self.pages = pages
        super().__init__(
            author_id,
            [embed for _, embed in pages],
            start,
            timeout=MENU_TIMEOUT,
            button_row=1,
        )

        options = [nextcord.SelectOption(label="Overview", value="Overview")]
        for name in dict.fromkeys(name for name, _ in pages if name is not None):
            options.append(nextcord.SelectOption(label=name[:100], value=name[:100]))
        # Discord needs a dropdown with a custom_id, so make a random one for it
        self.module_select = nextcord.ui.StringSelect(
            custom_id=os.urandom(16).hex(),
            placeholder=placeholder,
            options=options[:MAX_SELECT_OPTIONS],
            row=0,
        )
        self.module_select.callback = self.select_module
        self.add_item(self.module_select)

    async def select_module(self, interaction: nextcord.Interaction):
        chosen = self.module_select.values[0]
        for index, (name, _) in enumerate(self.pages):
            if (name or "Overview")[:100] == chosen:
                await self._show(interaction, index)
                return


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
        embed.description = (f"{description}\n\n" if description else "") + (
            f"Pick a module below, or use `{prefix}help [module]`, to see its commands. "
            f"Use `{prefix}help permissions` to see who can use which command."
        )

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

    def permission_pages(self) -> list:
        """An overview of the permission categories, then each category's commands by module.
        Lists every command, not just the ones the caller can use, so people can see what
        a role would get them."""
        prefix = self.context.clean_prefix
        by_category = {}
        for command in self.context.bot.commands:
            if command.hidden:
                continue
            category = command_predicates.permission_category(command)
            module = command.cog.qualified_name if command.cog else "No Module"
            by_category.setdefault(category, {}).setdefault(module, []).append(
                f"`{prefix}{command.name}`"
            )
        order = list(PERMISSION_PAGES)
        categories = sorted(
            by_category,
            key=lambda category: (
                order.index(category) if category in order else len(order),
                category,
            ),
        )

        overview = discord_utils.create_embed()
        overview.title = "Commands by Permission"
        overview.description = (
            "Who can use which command. Server admins give a role a category with "
            f"`{prefix}addperm`, e.g. `{prefix}addperm Solver @role`. A role only gets "
            "the commands of the categories it was added to.\n\n"
            f"Pick a category below, or use `{prefix}help [command]` for more on a command."
        )
        pages = [(None, overview)]
        for category in categories:
            title, who = PERMISSION_PAGES.get(category, (category, None))
            who = who and who.format(prefix=prefix)
            modules = by_category[category]
            count = sum(len(names) for names in modules.values())
            overview.add_field(
                name=title,
                value=f"{who + ' ' if who else ''}{count} command{'s' * (count != 1)}.",
                inline=False,
            )
            embed = discord_utils.create_embed()
            embed.title = f"{title} Commands"
            embed.description = who
            for module in sorted(modules):
                for chunk in chunk_names(sorted(modules[module])):
                    embed.add_field(name=module, value=chunk, inline=False)
            pages.append((title, embed))
        return pages

    async def send_permissions_help(self):
        """implements ~help permissions, the commands-by-permission menu"""
        await self.send_menu(self.permission_pages(), placeholder="Jump to a category")

    async def command_callback(
        self, ctx: commands.Context, *, command: str | None = None
    ):
        """Sends the commands-by-permission menu for ~help permissions, else the usual help."""
        if command is not None and command.strip().lower() in PERMISSION_WORDS:
            await self.prepare_help_command(ctx, command)
            return await self.send_permissions_help()
        return await super().command_callback(ctx, command=command)

    async def send_menu(
        self, pages: list, start: int = 0, placeholder: str = "Jump to a module"
    ):
        """Send pages as one public message with a HelpMenu, showing pages[start]."""
        for number, (_, embed) in enumerate(pages, start=1):
            embed.set_footer(
                text=f"Page {number}/{len(pages)} • {self.get_ending_note()}"
            )
        view = HelpMenu(self.context.author.id, pages, start, placeholder)
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
