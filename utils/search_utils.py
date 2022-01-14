# from  https://github.com/Moonrise55/Mbot/blob/f4e19df1df9fa4ef1a7730e63aa8009894aa304c/utils/paginator.py#L8

import discord
import asyncio


# set up pagination of results


class Pages:
    """
    (self, ctx, *, solutions, weights=None, embedTemp, endflag=None)
    solutions, weights: lists
    """

    def __init__(self, ctx, *, solutions, weights=None, embedTemp, endflag=None):
        self.bot = ctx.bot
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author
        self.solutions = solutions
        self.weights = weights
        self.endflag = endflag
        self.page = 1
        self.numsol = 15
        self.embed = embedTemp
        self.title = embedTemp.title
        self.description = None
        self.first = True
        self.loopState = True
        self.reactAll = [
            "\u23EA",  # first
            "\u25C0",  # left
            "\u25B6",  # right
            "\u274C",  # stop
        ]

    def extractData(self):
        final = []
        finalend = []
        start = (self.page - 1) * self.numsol
        end = start + self.numsol

        # check if request page empty
        if start > len(self.solutions):
            self.page = self.page - 1
            start = (self.page - 1) * self.numsol
            end = start + self.numsol

        # check if request page partial
        if end >= len(self.solutions):
            end = len(self.solutions)
            if self.endflag:
                finalend = self.endflag

        for n in range(start, end):
            if self.weights:
                line = (
                    self.solutions[n]
                    + "...................."
                    + str(round(self.weights[n], 3))
                )
            else:
                line = self.solutions[n]
            final.append(line)
        final = "\n".join(final)

        if finalend:
            final = final + "\n" + finalend

        return final

    async def sendPage(self):
        final = self.extractData()
        self.embed.description = final
        self.embed.title = self.title + " (pg:" + str(self.page) + ")"

        if self.first:
            self.message = await self.channel.send(embed=self.embed)
            self.first = False
        else:
            await self.message.edit(embed=self.embed)

        for react in self.reactAll:
            await self.message.add_reaction(react)

    async def pageLoop(self):
        def check(reaction, user):
            if user != self.author:
                return False
            if str(reaction.emoji) not in self.reactAll:
                return False
            if reaction.message.id != self.message.id:
                return False
            return True

        while self.loopState:
            await self.sendPage()

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=check, timeout=120.0
                )

            except asyncio.TimeoutError:
                await self.message.clear_reactions()
                self.loopState = False
                # await self.channel.send('I timed out')

            else:
                await self.message.remove_reaction(reaction, user)
                # await self.channel.send(reaction)

                if str(reaction.emoji) == self.reactAll[0]:
                    self.page = 1
                elif str(reaction.emoji) == self.reactAll[1]:
                    if self.page != 1:
                        self.page = self.page - 1
                elif str(reaction.emoji) == self.reactAll[2]:
                    self.page = self.page + 1
                elif str(reaction.emoji) == self.reactAll[3]:
                    await self.message.clear_reactions()
                    self.loopState = False
