import googlesearch
import discord
from discord.ext import commands
from utils import discord_utils
import constants
from modules.lookup import lookup_constants

#######
# TODO: DELETE wikipedia, google, and dcode now that search works
# Actually I think we should keep google as a default so they don't have to specify google everytime
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
            await ctx.send(discord_utils.create_no_argument_embed("Target Site and Query"))
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
        """Command to return 10 google results of the query"""
        print("Received google")
        if len(args) > 0:
            embed = discord_utils.create_embed()
            # Join args
            query = ' '.join(args)
            results = []
            for j in googlesearch.search(query, num=lookup_constants.QUERY_NUM,
                                         stop=lookup_constants.QUERY_NUM,
                                         pause=lookup_constants.PAUSE_TIME):
                results.append(j)
            embed.add_field(name='Search Results', value=f"Here's what I've found for {query}:\n"
                                                         f"{chr(10).join(results)}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord_utils.create_no_argument_embed())

    @commands.command(name="dcode")
    async def dcode(self, ctx, *args):
        """Command to return a dcode result (from google)"""
        print("Received dcode")
        if len(args) > 0:
            embed = discord_utils.create_embed()
            original_query = ' '.join(args)
            query = original_query + ' ' + lookup_constants.DCODE_FR
            wiki_link = None
            found_wiki_link = False
            # We only care about the first wikipedia link. But if we can't find one
            # Let's return the first dcode.fr link.
            for j in googlesearch.search(query,
                                         num=lookup_constants.QUERY_NUM,
                                         stop=lookup_constants.QUERY_NUM,
                                         pause=lookup_constants.PAUSE_TIME):
                if lookup_constants.DCODE_FR in j:
                    embed.add_field(name=f"{lookup_constants.DCODE_FR.capitalize()} Result!", value=j)
                    await ctx.send(embed=embed)
                    return
                if lookup_constants.WIKIPEDIA in j and not found_wiki_link:
                    wiki_link = j
                    found_wiki_link = True
            if found_wiki_link:
                embed.add_field(name=f"{lookup_constants.WIKIPEDIA.capitalize()} Result",
                                value=f"Sorry! Couldn't find a {lookup_constants.DCODE_FR} link for {original_query}.\n"
                                      f"Found a {lookup_constants.WIKIPEDIA} link: \n{wiki_link}")
            else:
                embed.add_field(name="No dice!", value=f"Sorry! Could not find a result for {original_query}")
        else:
            embed = discord_utils.create_no_argument_embed()
        await ctx.send(embed=embed)

    @commands.command(name="wikipedia")
    async def wikipedia(self, ctx, *args):
        """Command to return a wikipedia result (from google)"""
        print("Received wikipedia")
        if len(args) > 0:
            embed = discord_utils.create_embed()
            original_query = ' '.join(args)
            query = original_query + ' ' + lookup_constants.WIKIPEDIA
            wiki_link = None
            found_dcode_link = False
            # We only care about the first dcode link. But if we can't find one
            # Let's return the first wikipedia link.
            for j in googlesearch.search(query,
                                         num=lookup_constants.QUERY_NUM,
                                         stop=lookup_constants.QUERY_NUM,
                                         pause=lookup_constants.PAUSE_TIME):
                if lookup_constants.WIKIPEDIA in j:
                    embed.add_field(name=f"{lookup_constants.WIKIPEDIA.capitalize()} Result!", value=j)
                    await ctx.send(embed=embed)
                    return
                if lookup_constants.DCODE_FR in j and not found_dcode_link:
                    wiki_link = j
                    found_dcode_link = True
            if found_dcode_link:
                embed.add_field(name=f"{lookup_constants.DCODE_FR.capitalize()} Result",
                                value=f"Sorry! Couldn't find a {lookup_constants.WIKIPEDIA} link for {original_query}"
                                      f"Found a {lookup_constants.DCODE_FR} link \n{wiki_link}")
            else:
                embed.add_field(name="No dice!", value=f"Sorry! Could not find a result for {original_query}")
        else:
            embed = discord_utils.create_no_argument_embed()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LookupCog(bot))