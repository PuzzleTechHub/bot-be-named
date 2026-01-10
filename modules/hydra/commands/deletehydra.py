"""
deletehydra command - Deletes a puzzle channel, tab, and overview entry with confirmation.
"""

import asyncio

import emoji
import gspread
import nextcord
from nextcord.ext import commands

from modules.hydra import constants as hydra_constants
from modules.hydra.hydra_utils import hydra_helpers
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils
from utils import command_predicates, discord_utils, logging_utils, sheet_utils


def setup_cmd(cog):
    """Register the deletehydra command with the bot."""

    @command_predicates.is_trusted()
    @cog.bot.command(name="deletehydra")
    async def deletehydra(ctx: commands.Context, channel_mention: str = ""):
        """Deletes a puzzle channel, its corresponding tab, triggers archiving and cleans
        up the overview.

        Must be called from a different channel from the one being deleted.

        You'll need to confirm the deletion by reacting to the confirmation message within 15 seconds.

        Permission Category : Trusted Roles only.

        Usage: `~deletehydra #puzzle-channel` (deletes #puzzle-channel)
        """
        await logging_utils.log_command(
            "deletehydra", ctx.guild, ctx.channel, str(ctx.author)
        )
        embed = discord_utils.create_embed()

        # Check if channel mention is provided
        if channel_mention == "":
            embed.add_field(
                name="Failed",
                value="Please provide a channel to delete. Usage: `~deletehydra #puzzle-channel`",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Parse the channel from the mention
        target_channel = None
        if ctx.message.channel_mentions:
            target_channel = ctx.message.channel_mentions[0]

        if target_channel is None:
            embed.add_field(
                name="Failed",
                value="Please mention the channel, not just type its name!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Type guard: ensure target is a text channel
        if not isinstance(target_channel, nextcord.TextChannel):
            embed.add_field(
                name="Failed",
                value="Can only delete text channels.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Check that the target channel is not the same as the command channel
        if target_channel.id == ctx.channel.id:
            embed.add_field(
                name="Failed",
                value="You cannot delete the channel you are currently in. Please run this command from a different channel.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Check that the target channel has a valid sheet tether
        result, _ = sheet_utils.findsheettether(
            target_channel.category_id if target_channel.category_id else 0,
            target_channel.id,
        )

        if result is None:
            embed.add_field(
                name="Failed",
                value=f"The channel {target_channel.mention} is not tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        curr_sheet_link = str(result.sheet_link)

        # Confirmation prompt
        confirm_embed = discord_utils.create_embed()
        confirm_embed.add_field(
            name="Confirm deletion?",
            value=f"You are about to delete the channel {target_channel.mention} and its corresponding tab in the sheet.\n\n"
            f"This will:\n"
            f"- Archive the channel contents\n"
            f"- Delete the Discord channel\n"
            f"- Delete the tab from the Google Sheet\n"
            f"- Remove the entry from the Overview sheet\n\n"
            f"React with ✅ to confirm or ❌ to cancel.",
        )

        confirm_emoji = "✅"
        cancel_emoji = "❌"

        confirm_message = (await discord_utils.send_message(ctx, confirm_embed))[0]
        await confirm_message.add_reaction(confirm_emoji)
        await confirm_message.add_reaction(cancel_emoji)

        def check_correct_react(reaction, user):
            return (
                user == ctx.author
                and reaction.message.id == confirm_message.id
                and str(reaction.emoji) in ("✅", "❌")
            )

        try:
            reaction, _ = await cog.bot.wait_for(
                "reaction_add",
                timeout=hydra_constants.DELETE_CONFIRM_TIMEOUT,
                check=check_correct_react,
            )
        except asyncio.TimeoutError:
            timeout_embed = discord_utils.create_embed()
            timeout_embed.add_field(
                name="Cancelled!",
                value="No confirmation received in time. "
                f"{target_channel.mention} will not deleted.",
                inline=False,
            )
            await discord_utils.send_message(ctx, timeout_embed)
            return

        # If the user reacted with the cancel emoji, abort immediately.
        if str(reaction.emoji) == "❌":
            cancel_embed = discord_utils.create_embed()
            cancel_embed.add_field(
                name="Aborted!",
                value=f"Deletion aborted. {target_channel.mention} will not be deleted.",
                inline=False,
            )
            await discord_utils.send_message(ctx, cancel_embed)
            return

        # Proceed with deletehydra

        async with cog.lock:
            progress_embed = discord_utils.create_embed()
            progress_embed.add_field(
                name="Deletion in Progress",
                value=f"Deleting channel {target_channel.mention} and its corresponding tab. Please wait...",
                inline=False,
            )
            progress_msg = (await discord_utils.send_message(ctx, progress_embed))[0]

            try:
                # 1. Archive channel first
                archive_cmd = cog.bot.get_command("archivechannel")
                if archive_cmd:
                    await ctx.invoke(archive_cmd, target_channel.mention)
                else:
                    # Fallback
                    fallback_embed = discord_utils.create_embed()
                    fallback_embed.add_field(
                        name="Failed",
                        value="Could not find archivechannel command. Continuing without archiving.",
                        inline=False,
                    )
                    await discord_utils.send_message(ctx, fallback_embed)

                # 2. Get overview and find the row for this channel
                overview_sheet = await hydra_sheet_utils.get_overview(
                    cog.gspread_client, ctx, curr_sheet_link
                )

                tab_name = None
                row_to_find = None
                tab_name_found = False

                if overview_sheet is not None:
                    # We need to find the row by channel ID
                    list_chan_cells = await hydra_sheet_utils.findchanidcell(
                        cog.gspread_client,
                        ctx,
                        curr_sheet_link,
                        [target_channel.id],
                    )

                    if list_chan_cells and list_chan_cells[0][0] is not None:
                        row_to_find = list_chan_cells[0][0]

                        # Get tab name from the appropriate column
                        # Get the cell formula from column D
                        try:
                            tab_name = overview_sheet.get_cell_value(
                                f"D{row_to_find}"
                            )  # FIXME - hardcoded
                            tab_name_found = True
                        except (gspread.exceptions.APIError, IndexError):
                            tab_name_found = False

                # 3. Delete discord channel
                channel_name = target_channel.name
                await target_channel.delete(
                    reason=f"Deleted by {ctx.author} via `~deletehydra` command."
                )

                # 4. Delete tab from sheet (skip if tab name wasn't found anyway)
                tab_deleted = False
                if tab_name_found and tab_name:
                    try:
                        sh = cog.gspread_client.open_by_url(curr_sheet_link)

                        # Try to find and delete worksheet
                        ws_to_delete = None
                        if tab_name:
                            ws_to_delete = next(
                                (ws for ws in sh.worksheets() if ws.title == tab_name),
                                None,
                            )

                        if ws_to_delete:
                            sh.del_worksheet(ws_to_delete)
                            tab_deleted = True
                    except gspread.exceptions.APIError:  # Report in final message
                        pass
                    except Exception:
                        pass

                # 5. Delete overview row
                row_moved = False
                if overview_sheet is not None and row_to_find is not None:
                    try:
                        overview_ws = overview_sheet.worksheet

                        # Get the row values
                        overview_values = overview_sheet.overview_data
                        if row_to_find <= len(overview_values):
                            row_values = overview_values[row_to_find - 1]
                        else:
                            row_values = []

                        if row_values:
                            overview_ws.delete_rows(row_to_find)
                            # A new row probably should be created here, but
                            # the filter on the overview sheet doesnt apply
                            # properly, so we'll just trust the users good
                            # judgement to add more rows manually

                            row_moved = True

                    except gspread.exceptions.APIError:  # Report in final message
                        pass
                    except Exception:
                        pass

                # Delete progress message
                await progress_msg.delete()

                # 6. Send success message
                success_embed = discord_utils.create_embed()

                status_lines = []
                status_lines.append(
                    f"- ✅ Channel {channel_name} deleted successfully."
                )
                status_lines.append("- ✅ Archiving completed.")
                if tab_deleted:
                    status_lines.append(f"- ✅ Tab '{tab_name}' deleted from sheet.")
                else:
                    status_lines.append(
                        f"- ❌ Failed to delete tab '{tab_name}' from sheet."
                    )

                if row_moved:
                    status_lines.append("- ✅ Overview row deleted.")
                else:
                    status_lines.append("- ❌ Failed to delete overview row.")

                success_embed.add_field(
                    name="Report of deletion",
                    value="\n".join(status_lines),
                    inline=False,
                )

                await ctx.message.add_reaction(emoji.emojize(":check_mark_button:"))
                await discord_utils.send_message(ctx, success_embed)

            except gspread.exceptions.APIError as e:
                await hydra_helpers.handle_gspread_error(ctx, e, embed)
            except nextcord.Forbidden:
                embed.add_field(
                    name="Failed",
                    value="I do not have permission to delete the channel.",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
            except Exception as e:
                embed.add_field(
                    name="Failed",
                    value=f"An unknown error occurred: {str(e)}",
                    inline=False,
                )
                await discord_utils.send_message(ctx, embed)
