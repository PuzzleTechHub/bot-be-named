import nextcord
import urllib
import re
from utils.paging_utils import Pages
from nextcord.ext import commands
from utils import discord_utils

"""
Lookup module. Nutrimatic and similar puzzle-hunt lookups.
"""


class LookupCog(commands.Cog, name="Lookup"):
    """
    Nutrimatic and similar puzzle-hunt lookups.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nutrimatic", aliases=["n", "nu", "nut", "nutri"])
    async def nutrimatic(self, ctx: commands.Context, *, query=None):
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
            await discord_utils.send_message(ctx, embed)
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
