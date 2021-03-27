import googlesearch
import discord
from discord.ext import commands
from utils import discord_utils
import constants

#######
# TODO: Generalize Dcode and Wikipedia. Copy/pasted code
class LookupCog(commands.Cog, name="Lookup"):
    """Performs a Google Search (for ciphers etc)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="google")
    async def google(self, ctx, *args):
        """Command to return 10 google results of the query"""
        print("Received google")
        if len(args) > 0:
            embed = discord_utils.create_embed()
            # Join args
            query = ' '.join(args)
            results = []
            for j in googlesearch.search(query, num=constants.QUERY_NUM,
                                         stop=constants.QUERY_NUM,
                                         pause=constants.PAUSE_TIME):
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
            query = original_query + ' ' + constants.DCODE_FR
            wiki_link = None
            found_wiki_link = False
            # We only care about the first wikipedia link. But if we can't find one
            # Let's return the first dcode.fr link.
            for j in googlesearch.search(query,
                                         num=constants.QUERY_NUM,
                                         stop=constants.QUERY_NUM,
                                         pause=constants.PAUSE_TIME):
                if constants.DCODE_FR in j:
                    embed.add_field(name=f"{constants.DCODE_FR.capitalize()} Result!", value=j)
                    await ctx.send(embed=embed)
                    return
                if constants.WIKIPEDIA in j and not found_wiki_link:
                    wiki_link = j
                    found_wiki_link = True
            if found_wiki_link:
                embed.add_field(name=f"{constants.WIKIPEDIA.capitalize()} Result",
                                value=f"Sorry! Couldn't find a {constants.DCODE_FR} link for {original_query}.\n"
                                      f"Found a {constants.WIKIPEDIA} link: \n{wiki_link}")
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
            query = original_query + ' ' + constants.WIKIPEDIA
            wiki_link = None
            found_dcode_link = False
            # We only care about the first dcode link. But if we can't find one
            # Let's return the first wikipedia link.
            for j in googlesearch.search(query,
                                         num=constants.QUERY_NUM,
                                         stop=constants.QUERY_NUM,
                                         pause=constants.PAUSE_TIME):
                if constants.WIKIPEDIA in j:
                    embed.add_field(name=f"{constants.WIKIPEDIA.capitalize()} Result!", value=j)
                    await ctx.send(embed=embed)
                    return
                if constants.DCODE_FR in j and not found_dcode_link:
                    wiki_link = j
                    found_dcode_link = True
            if found_dcode_link:
                embed.add_field(name=f"{constants.DCODE_FR.capitalize()} Result",
                                value=f"Sorry! Couldn't find a {constants.WIKIPEDIA} link for {original_query}"
                                      f"Found a {constants.DCODE_FR} link \n{wiki_link}")
            else:
                embed.add_field(name="No dice!", value=f"Sorry! Could not find a result for {original_query}")
        else:
            embed = discord_utils.create_no_argument_embed()
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LookupCog(bot))