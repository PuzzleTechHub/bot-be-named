"""
watchcategoryhydra command - Summarizes recent messages across categories.
"""

import heapq
from collections import Counter

import constants
from modules.hydra import constants as hydra_constants
from utils import command_predicates, discord_utils, logging_utils


def setup_cmd(cog):
    """Register the watchcategoryhydra command with the bot."""

    @command_predicates.is_solver()
    @cog.bot.command(
        name="watchcategoryhydra",
        aliases=["watchcathydra", "watchcat", "watchcategory"],
    )
    async def watchcategoryhydra(ctx, *args):
        """Summarise the last `limit` messages across one or more categories:
        `limit` caps off at 250.
        Note: Will pick up messages to which the command user does not have access to.
        Only counts messages from humans (not bots).

        Permission Category : Solver Roles only.
        Usage: `~watchcategoryhydra [category names] [limit]`
        Usage: `~watchcategoryhydra` (current category, limit 100)
        Usage: `~watchcategoryhydra 50` (current category, limit 50)
        Usage: `~watchcategoryhydra "Cat 1" "Cat 2"` (multiple categories, limit 100)
        Usage: `~watchcategoryhydra "Cat 1" "Cat 2" 50` (multiple categories, limit 50)
        """

        await logging_utils.log_command(
            "watchcategoryhydra", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Parse arguments
        limit = hydra_constants.WATCH_DEFAULT_LIMIT
        category_names = []

        if args:
            # Check if last arg is an integer (limit)
            try:
                limit = int(args[-1])
                category_names = list(args[:-1])
            except ValueError:
                # Last arg is not an integer, all args are category names
                category_names = list(args)

        if limit > hydra_constants.WATCH_MAX_LIMIT:
            limit = hydra_constants.WATCH_MAX_LIMIT

        # Determine which categories to watch
        categories = []
        if not category_names:
            # No categories specified, use current channel's category
            currcat = ctx.message.channel.category
            if currcat is None:
                embed.add_field(
                    name="Failed",
                    value="You must call this command from a channel in a category, or specify category names.",
                )
                await discord_utils.send_message(ctx, embed)
                return
            categories = [currcat]
        else:
            # Find each specified category
            for cat_name in category_names:
                cat = await discord_utils.find_category(ctx, cat_name)
                if cat is None:
                    embed.add_field(
                        name="Failed",
                        value=f"I cannot find category `{cat_name}`. Perhaps check your spelling and try again.",
                    )
                    await discord_utils.send_message(ctx, embed)
                    return
                categories.append(cat)

        start_embed = discord_utils.create_embed()
        cat_names = ", ".join([f"`{cat.name}`" for cat in categories])
        start_embed.add_field(
            name="Summary Started",
            value=f"Your summarizing of {len(categories)} categor{'ies' if len(categories) > 1 else 'y'} ({cat_names})"
            f" has begun! This may take a while. If I run into "
            f"any errors, I'll let you know.",
            inline=False,
        )

        start_msg = (await discord_utils.send_message(ctx, start_embed))[0]

        embed = discord_utils.create_embed()

        try:
            # 1. Fetch initial messages from each channel across categories given
            channel_histories = []
            for cat in categories:
                for ch in cat.text_channels:
                    try:
                        history = []
                        async for m in ch.history(
                            limit=hydra_constants.HISTORY_FETCH_LIMIT
                        ):
                            history.append(m)
                        if history:
                            channel_histories.append(
                                (ch, history, 0)
                            )  # (channel, messages, current_index)
                    except Exception:
                        # Skip channels we can't read
                        continue

            # 2. Initialize Min-Heap with the first message from each channel
            min_heap = []
            for ch, history, idx in channel_histories:
                if history:
                    msg = history[idx]
                    # Push (timestamp, channel_index, message) - using negative timestamp for max-heap behavior
                    heapq.heappush(
                        min_heap,
                        (-msg.created_at.timestamp(), len(min_heap), ch, history, idx),
                    )

            # 3. Extract human messages and non bot calls until we have enough
            msgs = []
            channel_indices = {ch: i for i, (ch, _, _) in enumerate(channel_histories)}

            while min_heap and len(msgs) < limit:
                # Get the most recent message
                _, _, ch, history, idx = heapq.heappop(min_heap)
                current_msg = history[idx]

                # Check if it's from a human (not a bot)
                if not current_msg.author.bot and not current_msg.content.startswith(
                    constants.DEFAULT_BOT_PREFIX
                ):
                    msgs.append(
                        (
                            current_msg.created_at,
                            ch,
                            current_msg.author,
                            current_msg.content,
                        )
                    )

                # Refill the heap from the same channel
                next_idx = idx + 1
                if next_idx < len(history):
                    next_msg = history[next_idx]
                    heapq.heappush(
                        min_heap,
                        (
                            -next_msg.created_at.timestamp(),
                            channel_indices.get(ch, 0),
                            ch,
                            history,
                            next_idx,
                        ),
                    )

        except Exception as e:
            embed.add_field(
                name="Failed",
                value=f"An error occurred while fetching messages. Error: {str(e)}",
                inline=False,
            )
            await discord_utils.send_message(ctx, embed)
            return

        # Delete start message
        if start_msg:
            await start_msg.delete()

        # aggregate
        channel_counts = Counter()
        author_counts = Counter()
        for _, ch, author, _ in msgs:
            channel_counts[ch.mention] += 1
            author_counts[author.mention] += 1

        total = len(msgs)
        total_channels = sum(len(cat.text_channels) for cat in categories)
        embed.add_field(
            name="Summary",
            value=f"Analyzed {total} human messages across {total_channels} channels in {len(categories)} categor{'ies' if len(categories) > 1 else 'y'} ({cat_names}).",
            inline=False,
        )
        await discord_utils.send_message(ctx, embed)
        embed = discord_utils.create_embed()

        if channel_counts:
            ch_lines = [
                f"- {ch_mention}: {count} message{'s' if count != 1 else ''}"
                for ch_mention, count in channel_counts.most_common()
            ]
            embed.add_field(
                name="By channel",
                value="\n".join(ch_lines),
                inline=False,
            )
        await discord_utils.send_message(ctx, embed)
        embed = discord_utils.create_embed()

        if author_counts:
            author_lines = [
                f"- {author_mention}: {count} message{'s' if count != 1 else ''}"
                for author_mention, count in author_counts.most_common()
            ]
            embed.add_field(
                name="By author",
                value="\n".join(author_lines),
                inline=False,
            )

        await discord_utils.send_message(ctx, embed)
