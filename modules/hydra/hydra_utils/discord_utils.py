from utils import discord_utils
import constants
import nextcord
from nextcord.ext.commands import Context


async def category_move_to_archive(ctx: Context, archive_name: str):
    """Moves the current channel to an archive category, or archives the thread if called from a thread.
    1. Takes the current channel's category name, and splits it into words. Looks for (all words) Archive, then (all but last word) Archive,
    then (all but last two words) Archive etc.

    2. Once it finds a candidate category, moves the channel to that category.

    3. If the candidate category is full, create a new category with the same name, but with 2 appended to the end.

    4. If the candidate category is full but the category with 2 appended to the end also exists and is full, try with 3, etc.
    """
    embed = discord_utils.create_embed()
    # Handling if mta is called from a thread
    if await discord_utils.is_thread(ctx, ctx.channel):
        # Checking if thread can be archived by the bot
        try:
            await ctx.channel.edit(archived=True)
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value="Forbidden! Have you checked if the bot has the required permissions?",
            )
            await discord_utils.send_message(ctx, embed)
            return
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Archived {ctx.channel.mention} thread",
            inline=False,
        )
        await ctx.channel.edit(archived=True)
        await discord_utils.send_message(ctx, embed)
        return

    # Otherwise mta is called from a regular channel
    archive_category = None
    candidates = []
    if archive_name is None:
        # Find category with same name + Archive (or select combinations)
        cat_name = ctx.channel.category.name
        cat_name_words = cat_name.split(" ")

        for i in range(len(cat_name_words), 0, -1):
            candidate = " ".join(cat_name_words[:i]) + " Archive"
            candidates.append(candidate)

        for cand in candidates:
            archive_category = await discord_utils.find_category(ctx, cand)
            if archive_category:
                break

    else:
        archive_category = await discord_utils.find_category(ctx, archive_name)

    if archive_category is None:
        if archive_name is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"I can't find the archive, so I cannot move {ctx.channel.mention}. "
                "I checked for the following categories: "
                + ", ".join(f"`{c}`" for c in candidates),
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return
        else:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"There is no category named `{archive_name}`, so I cannot move {ctx.channel.mention}.",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

    if discord_utils.category_is_full(archive_category):
        # Search for all categories that start with archive_category.name.
        categories_starting_with_name = []
        category_found = False

        for category in ctx.guild.categories:
            if category.name.startswith(archive_category.name):
                categories_starting_with_name.append(category)

        for category in categories_starting_with_name:
            if not discord_utils.category_is_full(category):
                archive_category = category
                category_found = True
                break

        if not category_found:
            clonecat = ctx.bot.get_command("clonecat")
            category_to_make = (
                f"{archive_category.name} {len(categories_starting_with_name) + 1}"
            )

            await ctx.invoke(
                clonecat,
                origCatName=archive_category.name,
                targetCatName=category_to_make,
            )
            embed.add_field(
                name=f"Created new archive category!",
                value=f"Archive category `{archive_category.name}` is full, so created new category `{category_to_make}`!",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)

            embed = discord_utils.create_embed()  # Reset embed
            archive_category = await discord_utils.find_category(
                ctx, category_to_make
            )  # Change it to the new one!

    if archive_category == ctx.channel.category:
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Archive category `{archive_category.name}` is the same as current category `{ctx.channel.category.name}`. No need to move channel!",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return

    try:
        # move channel
        await ctx.channel.edit(category=archive_category)
        await ctx.channel.edit(position=1)
    except nextcord.Forbidden:
        embed.add_field(
            name=f"{constants.FAILED}!",
            value=f"Can you check my permissions? I can't seem to be able to move "
            f"{ctx.channel.mention} to `{archive_category.name}`",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        return

    embed.add_field(
        name=f"{constants.SUCCESS}!",
        value=f"Moved channel {ctx.channel.mention} to `{archive_category.name}`",
        inline=False,
    )
    await discord_utils.send_message(ctx, embed)
