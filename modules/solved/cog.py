import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
import modules.code.utils as utils

class SolvedCog(commands.Cog):
	"""Checks for `solved` and `unsolved` command
	Toggles `solved-` prefix on channel name"""

	def __init__(self, bot):
		self.bot = bot
		self.prefix = "solved"

	@commands.command(name="solved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solved(self, ctx):
		"""Changes channel name to solved-<channel-name>"""
		# log command in console
		print("Received solved")
		embed = utils.create_embed()
		# get channel
		channel = ctx.message.channel
		# create prefix checking object
		p = Prefix(channel, self.prefix)
		# check if already solved
		if not p.has_prefix():
			new_channel_name = p.add_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as solved!")
			# reply to user
			await ctx.send(embed=embed)
			# rename channel to append prefix
			await channel.edit(name=new_channel_name)
		# already solved
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"Channel already marked as solved!")
			# reply to user
			await ctx.send(embed=embed)

	@commands.command(name="unsolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def unsolved(self, ctx):
		"""removed solved prefix from channel name"""
		# log command in console
		print("Received unsolved")
		embed = utils.create_embed()
		# get channel
		channel = ctx.message.channel
		# create prefix checking object
		p = Prefix(channel, self.prefix)
		# check if already solved
		if p.has_prefix():
			# edit channel name to remove prefix
			new_channel_name = p.remove_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as unsolved!")
			# reply to user
			await ctx.send(embed=embed)
			# rename channel to remove prefix
			await channel.edit(name=new_channel_name)
		# already solved
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"Channel is not solved!")
			# reply to user
			await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(SolvedCog(bot))
