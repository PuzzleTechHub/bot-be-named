from typing import List

import nextcord
from nextcord.ext import commands


class CategoryDropdown(nextcord.ui.Select["SelectCategoryView"]):
    def __init__(self, categories: List[nextcord.CategoryChannel]):
        self.selected_category = None
        self._categories = {str(category.id): category for category in categories}
        options = [
            nextcord.SelectOption(label=category.name, value=str(category.id))
            for category in categories
        ]
        super().__init__(
            placeholder="Chose a category",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, _: nextcord.Interaction):
        self.selected_category = self._categories[self.values[0]]
        assert self.view is not None
        self.view.stop()


class SelectCategoryView(nextcord.ui.View):
    def __init__(self, categories: list, ctx: commands.Context):
        super().__init__()
        self._ctx = ctx
        self._author = ctx.author
        self.dropdown = CategoryDropdown(categories)
        self.add_item(self.dropdown)

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        """Returns true if the interaction with the view is allowed."""
        # Check if the interaction is from the author
        assert interaction.user is not None
        return self._author.id == interaction.user.id
