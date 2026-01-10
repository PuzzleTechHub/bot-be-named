"""
unmtahydra command - Moves channel from archive back to main hunt category.
"""

import re

import gspread
import nextcord
from nextcord.ext import commands

from modules.hydra.hydra_utils import hydra_helpers
from modules.hydra.hydra_utils.sheet_command_base import SheetCommandBase
from utils import (
    command_predicates,
    discord_utils,
    logging_utils,
    sheet_utils,
    sheets_constants,
)


def setup_cmd(cog):
    """Register the unmtahydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(name="unmtahydra")
    async def unmtahydra(ctx: commands.Context, category_name: str = ""):
        """Does the rough opposite of ~mtahydra. Moves the channel into the main hunt category and moves the sheet into the active section.
        If I cannot find the main hunt category, I will ask the user to specify it.

        Permission Category : Solver Roles only.
        Usage: `~unmtahydra`
        Usage: `~unmtahydra "Main Hunt Category Name"` (If I cannot find the main hunt category automatically)
        """
        await logging_utils.log_command(
            "unmtahydra", ctx.guild, ctx.channel, str(ctx.author)
        )

        # Type guard: ensure we're in a guild text channel
        if not isinstance(ctx.channel, nextcord.TextChannel):
            embed = discord_utils.create_embed()
            embed.add_field(
                name="Failed",
                value="This command can only be used in a guild (server) text channel.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        base = SheetCommandBase(ctx, cog.gspread_client)
        curr_sheet_link, overview_sheet, row_to_find = await base.get_sheet_context()

        if overview_sheet is None or row_to_find is None:
            return

        embed = discord_utils.create_embed()

        sheet_tab_id_col = sheets_constants.SHEET_TAB_ID_COLUMN
        try:
            overview_values = overview_sheet.overview_data
            _, col_idx = gspread.utils.a1_to_rowcol(sheet_tab_id_col + "1")
            sheet_tab_id = overview_values[row_to_find - 1][col_idx - 1]
        except Exception:
            embed.add_field(
                name="Failed",
                value=f"Could not find the Sheet Tab ID for channel {ctx.channel.mention} in the Overview sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        if ctx.channel.category is None:
            embed.add_field(
                name="Failed",
                value=f"The channel {ctx.channel.mention} is not in a category.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Find the main hunt category. We will first check if an argument was passed. Then, look for a category tethered to the
        # same sheet. If that fails, we get the current category's name, and remove "Archive" and look for that. Else, we will
        # just ask the user for the category name.

        main_category = None

        if category_name != "":
            main_category = await discord_utils.find_category(ctx, category_name)
            if main_category is None:
                embed.add_field(
                    name="Failed",
                    value=f"I cannot find category `{category_name}`. Perhaps check your spelling and try again.",
                )
                await discord_utils.send_message(ctx, embed)
                return

        if main_category is None:
            if ctx.guild is None:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="Failed",
                    value="This command must be used in a guild (server).",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

            for category in ctx.guild.categories:
                if category.id == ctx.channel.category.id:
                    continue  # Skip current category
                cat_result, _ = sheet_utils.findsheettether(category.id, 0)
                if (
                    cat_result is not None
                    and str(cat_result.sheet_link) == curr_sheet_link
                ):
                    main_category = category
                    break

        if main_category is None:
            if ctx.guild is None:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name="Failed",
                    value="This command must be used in a guild (server).",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
                return

            curr_cat_name = ctx.channel.category.name
            base_name = re.sub(r"\s*Archive\s*\d*$", "", curr_cat_name).strip()
            split_base_names = base_name.split()
            possible_category_prefixes = [
                " ".join(split_base_names[: len(split_base_names) - i])
                for i, _ in enumerate(split_base_names)
            ]

            possible_solving_categories = []
            # Look for categories that begin with the exact base name, then the bas name minus last word, etc.
            for possible_base_name in possible_category_prefixes:
                to_add_candidates = [
                    category
                    for category in ctx.guild.categories
                    if category.name.startswith(possible_base_name)
                    and not re.match(r".*Archive\s*\d*$", category.name)
                ]

                for candidate in to_add_candidates:
                    if candidate not in possible_solving_categories:
                        possible_solving_categories.append(candidate)

            if len(possible_solving_categories) == 1:
                main_category = possible_solving_categories[0]
            elif len(possible_solving_categories) > 1:
                # Collate list into embed so user can pick
                selection_embed = discord_utils.create_embed()
                selection_embed.add_field(
                    name="Multiple possible main hunt categories found",
                    value='Please specify which category to move the channel to by using `~unmtahydra "Category Name"`.\n\n'
                    + "\n".join(
                        [f"- {cat.name}" for cat in possible_solving_categories]
                    ),
                )
                await discord_utils.send_message(ctx, selection_embed)
                return

        if main_category is None:
            embed.add_field(
                name="Failed",
                value="I could not automatically find the main hunt category. \n"
                "Please specify the main hunt category name as an argument.",
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Try to move the channel
        channel_embed = discord_utils.create_embed()
        try:
            await ctx.channel.edit(category=main_category)
            channel_embed.add_field(
                name="Success",
                value=f"Successfully moved channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
        except nextcord.Forbidden:
            channel_embed.add_field(
                name="Failed",
                value=f"I do not have permission to move the channel {ctx.channel.mention} to category `{main_category.name}`.",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
            return
        except Exception as e:
            channel_embed.add_field(
                name="Failed",
                value=f"Could not move channel {ctx.channel.mention} to category `{main_category.name}`. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, channel_embed)
            return

        # Move the sheet tab into the active section
        tab_embed = discord_utils.create_embed()

        # Type check for curr_sheet_link
        if curr_sheet_link is None:
            tab_embed.add_field(
                name="Failed",
                value="Could not find sheet link.",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
            return

        try:
            curr_sheet = cog.gspread_client.open_by_url(curr_sheet_link)

            # Find index by looking for last occurrence of a sheet ending with "Template".
            all_sheets = curr_sheet.worksheets()
            template_index = 0
            found_template = False
            for sheet in all_sheets:
                if sheet.title.endswith("Template"):
                    template_index = sheet.index
                    found_template = True
                else:
                    if found_template:
                        break  # We found the last template already

            if not found_template:
                template_index = 0  # Move to start if no templates found

            # Use batch update to move the sheet
            curr_sheet.batch_update(
                {
                    "requests": [
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": int(sheet_tab_id),
                                    "index": template_index + 1,
                                },
                                "fields": "index",
                            }
                        }
                    ]
                }
            )
            tab_embed.add_field(
                name="Success",
                value=f"Successfully moved the sheet tab for {ctx.channel.mention} to the active section.",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
        except gspread.exceptions.APIError as e:
            await hydra_helpers.handle_gspread_error(ctx, e, tab_embed)
            return
        except Exception as e:
            tab_embed.add_field(
                name="Failed",
                value=f"Unknown error when moving tab: `{str(e)}`",
                inline=False,
            )
            await discord_utils.send_message(ctx, tab_embed)
            return
