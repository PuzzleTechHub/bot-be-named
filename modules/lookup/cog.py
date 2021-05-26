import googlesearch
from discord.ext import commands
from utils import discord_utils
from modules.lookup import lookup_constants, lookup_utils


class LookupCog(commands.Cog, name="Lookup"):
    """Performs a Google Search (for ciphers etc)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search")
    async def search(self, ctx, *args):
        """
        Command to search the interwebs! (google)
        Usage: ~search <target_site> <[query...]>
        """
        print("Received search")
        if len(args) < 2:
            await ctx.send(embed=discord_utils.create_no_argument_embed("Target Site and Query"))
            return
        target_site = args[0].lower()
        if target_site in lookup_constants.REGISTERED_SITES:
            target_site = lookup_constants.REGISTERED_SITES[target_site]
        # If we do a google search, we want to return the 10 top results
        # Otherwise, we want to just send the most relevant result
        if target_site == lookup_constants.GOOGLE:
            is_google_search = True
        else:
            is_google_search = False

        original_query = ' '.join(args[1:])
        # Don't add google to the query but add any other target site for easier access/SEO
        if not is_google_search:
            query = original_query + ' ' + target_site
        else:
            query = original_query
        # Dude this loop is going to be horrible wtf
        # If google:
        #   Store all results as a list and print them out line by line in an embed
        # If not google:
        #   Find the first result that matches the target site and return that
        #   If we can't find it, return the google query I think
        embed = discord_utils.create_embed()
        results = []
        for result in googlesearch.search(query, num=lookup_constants.QUERY_NUM,
                                          stop=lookup_constants.QUERY_NUM,
                                          pause=lookup_constants.PAUSE_TIME):
            if target_site in result:
                embed.add_field(name=f"{target_site.capitalize()} Result for {original_query}",
                                value=result)
                await ctx.send(embed=embed)
                return
            results.append(result)
        if is_google_search:
            embed.add_field(name=f"{target_site.capitalize()} Result for {original_query}",
                            value = f"{chr(10).join(results)}")
        else:
            embed.add_field(name=f"Search failed!", value=f"Sorry! We weren't able to find a {target_site.capitalize()}"
                                                          f"link for {original_query}. However, here are the top 10 hits on Google:\n"
                                                          f"{chr(10).join(results)}")
        await ctx.send(embed=embed)

    @commands.command(name="google")
    async def google(self, ctx, *args):
        print("Received google")
        results = lookup_utils.search_query(' '.join(args))

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Google Result for {' '.join(args)}",
                        value=f"{chr(10).join(results)}")
        await ctx.send(embed=embed)

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia(self, ctx, *args):
        print("Received wikipedia")
        results = lookup_utils.search_query(' '.join(args), target_site=lookup_constants.WIKI)

        embed = discord_utils.create_embed()
        if len(results) > 1:
            embed.add_field(name=f"Search failed!",
                            value=f"Sorry! We weren't able to find a Wikipedia"
                                  f"link for {' '.join(args)}. However, here are the top 10 hits on Google:\n"
                                  f"{chr(10).join(results)}")
        else:
            embed.add_field(name=f"Wikipedia Result for {' '.join(args)}",
                            value=f"{chr(10).join(results)}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LookupCog(bot))
