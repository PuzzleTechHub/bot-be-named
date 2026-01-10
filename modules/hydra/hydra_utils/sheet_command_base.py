from utils import discord_utils, sheet_utils
from modules.hydra.hydra_utils import sheet_utils as hydra_sheet_utils


class SheetCommandBase:
    """Base class for commands that interact with overview sheets"""

    def __init__(self, ctx, gspread_client):
        self.ctx = ctx
        self.gspread_client = gspread_client
        self.embed = discord_utils.create_embed()

    async def get_sheet_context(self):
        """Returns (sheet_link, overview_sheet, row_num) or (None, None, None) on error"""
        result, _ = sheet_utils.findsheettether(
            self.ctx.message.channel.category_id, self.ctx.message.channel.id
        )

        if result is None:
            self.embed.add_field(
                name="Failed",
                value=f"Neither the category **{self.ctx.message.channel.category.name}** "
                f"nor the channel {self.ctx.message.channel.mention} are tethered to any Google sheet.",
                inline=False,
            )
            await discord_utils.send_message(self.ctx, self.embed)
            return None, None, None

        curr_sheet_link = str(result.sheet_link)
        overview_sheet = await hydra_sheet_utils.get_overview(
            self.gspread_client, self.ctx, curr_sheet_link
        )

        if overview_sheet is None:
            return None, None, None

        row_to_find, err_embed = overview_sheet.find_row_of_channel(self.ctx)
        if err_embed is not None:
            await discord_utils.send_message(self.ctx, err_embed)
            return None, None, None

        return curr_sheet_link, overview_sheet, row_to_find
