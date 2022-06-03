import nextcord
from nextcord.ext import commands

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
        """Creates a button for creating a confessional channels"""
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server")
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


def setup(bot: commands.Bot):
    bot.add_cog(ConfessionalRequest(bot))
