import constants
from discord.ext import commands
import modules.code.code_utils as utils


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class CreateChannelCog(commands.Cog, name="Create Channel"):
	"""Checks for `createchannel` command
	Creates channel in same category with given name"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="createchannel")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
		constants.TA_VERIFIED_PUZZLER_ROLE_ID
	)
	async def createchannel(self, ctx, name: str = ""):
		"""Command to create channel in same category with given name"""
		# log command in console
		print("Received createchannel")
		embed = utils.create_embed()
		# check for channel name argument
		if len(name) > 0:
			# get guild and category
			guild = ctx.message.guild
			category = ctx.channel.category
			# create channel
			channel = await guild.create_text_channel(name, category=category)
			embed.add_field(name="Success!", value=f"Created channel {channel.mention} in {category}!")
			# reply to user
			await ctx.send(embed=embed)
		# no argument passed
		else:
			embed.add_field(name="Failed!", value=f"You must specify a channel name!")
			# reply to user
			await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(CreateChannelCog(bot))
