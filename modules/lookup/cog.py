import googlesearch
from nextcord.ext import commands
from utils import discord_utils, logging_utils
from modules.lookup import lookup_constants, lookup_utils
import nextcord
import urllib
from utils.search_utils import Pages
import re


class LookupCog(commands.Cog, name="Lookup"):
    """Performs a Google Search"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search")
    async def search(self, ctx, target_site: str, *args):
        """
        Command to search the interwebs! (google)

        Usage: `~search <target_site> <[query...]>`
        """
        logging_utils.log_command("search", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if len(args) < 1:
            await ctx.send(embed=discord_utils.create_no_argument_embed("Query"))
            return

        target_site = target_site.lower()
        if target_site in lookup_constants.REGISTERED_SITES:
            target_site = lookup_constants.REGISTERED_SITES[target_site]
        # If we do a google search, we want to return the 10 top results
        # Otherwise, we want to just send the most relevant result
        if target_site == lookup_constants.GOOGLE:
            is_google_search = True
        else:
            is_google_search = False

        original_query = " ".join(args)
        # Don't add google to the query but add any other target site for easier access/SEO
        if not is_google_search:
            query_with_site = original_query + " " + target_site
        else:
            query_with_site = original_query
        # Dude this loop is going to be horrible wtf
        # If google:
        #   Store all results as a list and print them out line by line in an embed
        # If not google:
        #   Find the first result that matches the target site and return that
        #   If we can't find it, return the google query I think
        results = []
        for result in googlesearch.search(
            query_with_site,
            num=lookup_constants.QUERY_NUM,
            stop=lookup_constants.QUERY_NUM,
            pause=lookup_constants.PAUSE_TIME,
        ):
            if target_site in result:
                embed.add_field(
                    name=f"{target_site.capitalize()} Result for {original_query}",
                    value=result,
                )
                await ctx.send(embed=embed)
                return
            results.append(result)
        if is_google_search:
            embed.add_field(
                name=f"{target_site.capitalize()} Result for {original_query}",
                value=f"{chr(10).join(results)}",
            )
        else:
            embed.add_field(
                name=f"Search failed!",
                value=f"Sorry! We weren't able to find a {target_site.capitalize()}"
                f"link for {original_query}. However, here are the top 10 hits on Google:\n"
                f"{chr(10).join(results)}",
            )
        await ctx.send(embed=embed)

    @commands.command(name="google")
    async def google(self, ctx, *args):
        """
        Command to search google!

        Usage: `~google <[query...]>`
        """
        logging_utils.log_command("google", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        results = lookup_utils.search_query(" ".join(args))

        embed.add_field(
            name=f"Google Result for {' '.join(args)}", value=f"{chr(10).join(results)}"
        )
        await ctx.send(embed=embed)

    @commands.command(name="wikipedia", aliases=["wiki"])
    async def wikipedia(self, ctx, *args):
        """
        Command to search Wikipedia!

        Usage: `~wikipedia <[query...]>`
        """
        logging_utils.log_command("wikipedia", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        results = lookup_utils.search_query(
            " ".join(args), target_site=lookup_constants.WIKI
        )

        if len(results) > 1:
            embed.add_field(
                name=f"Search failed!",
                value=f"Sorry! We weren't able to find a Wikipedia"
                f"link for {' '.join(args)}. However, here are the top 10 hits on Google:\n"
                f"{chr(10).join(results)}",
            )
        else:
            embed.add_field(
                name=f"Wikipedia Result for {' '.join(args)}",
                value=f"{chr(10).join(results)}",
            )
        await ctx.send(embed=embed)

    @commands.command(
        aliases=[
            "n",
            "nu",
            "nut",
            "nutr",
            "nutri",
            "nutrim",
            "nutrima",
            "nutrimat",
            "nutrimati",
        ]
    )
    async def nutrimatic(self, ctx, *, query=None):
        if not query:
            await ctx.send('Example regex: `!nut "<asympote_>"`')
            return

        query = query.replace("`", "")
        query = query.replace("\\", "")

        query_initial = query[:]
        query = (
            query_initial.replace("&", "%26")
            .replace("+", "%2B")
            .replace("#", "%23")
            .replace(" ", "+")
        )  # html syntax
        url = "https://nutrimatic.org/?q=" + query + "&go=Go"
        text = urllib.request.urlopen(url).read()
        text1 = text.decode()

        # set up embed template
        embed = nextcord.Embed(
            title="Your nutrimatic link", url=url, colour=nextcord.Colour.magenta()
        )
        embed.set_footer(text="Query: " + query_initial)

        # parse for solution list
        posA = [m.start() for m in re.finditer("<span", text1)]
        posB = [m.start() for m in re.finditer("</span", text1)]

        # check for no solutions, send error
        if not posA:
            final = "None"
            errA = [m.start() for m in re.finditer("<b>", text1)]
            errB = [m.start() for m in re.finditer("</b>", text1)]
            final = text1[errA[-1] + 3 : errB[-1]]
            if final.find("font") != -1:
                errA = [m.start() for m in re.finditer("<font", text1)]
                errB = [m.start() for m in re.finditer("</font>", text1)]
                final = text1[errA[-1] + 16 : errB[-1]]
            embed.description = final
            await ctx.send(embed=embed)
            return

        # check for ending error message, usually bolded
        # max number of solutions on a nutrimatic page is 100
        finalend = None
        if len(posA) < 100:
            try:
                errA = [m.start() for m in re.finditer("<b>", text1)]
                errB = [m.start() for m in re.finditer("</b>", text1)]
                finalend = text1[errA[-1] + 3 : errB[-1]]
            except:
                pass

        # prep solution and weights for paginator
        solutions = []
        weights = []
        for n in range(0, min(len(posA), 200)):
            word = text1[posA[n] + 36 : posB[n]]
            size = float(text1[posA[n] + 23 : posA[n] + 32])
            solutions.append(word)
            weights.append(size)

        p = Pages(
            ctx, solutions=solutions, weights=weights, embedTemp=embed, endflag=finalend
        )
        await p.pageLoop()


def setup(bot):
    bot.add_cog(LookupCog(bot))
