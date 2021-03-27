import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
import modules.code.utils as utils


class SolvedCog(commands.Cog):
	"""Checks for `solved` and `unsolved` command
	Toggles `solved-` prefix on channel name"""
	def __init__(self, bot):
		self.bot = bot

	def add_prefix(self, channel, prefix):
		"""Adds prefix to channel name"""
		embed = utils.create_embed()
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = str(channel)
		# check if already solved
		if not p.has_prefix():
			new_channel_name = p.add_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as {prefix}!")
		# already solved
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"Channel already marked as {prefix}!")
		return embed, new_channel_name

	def remove_prefix(self, channel, prefix):
		"""Remove prefix from channel name"""
		embed = utils.create_embed()
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = str(channel)
		# check if already solved
		if p.has_prefix():
			# edit channel name to remove prefix
			new_channel_name = p.remove_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as {prefix}!")
		# already has prefix
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"Channel is not marked as {prefix}!")
		return embed, new_channel_name

	@commands.command(name="solved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solved(self, ctx):
		"""Changes channel name to solved-<channel-name>"""
		# log command in console
		print("Received solved")
		channel = ctx.message.channel
		embed, new_channel_name = self.add_prefix(channel, constants.SOLVED_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="unsolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def unsolved(self, ctx):
		"""removes solved prefix from channel name"""
		# log command in console
		print("Received unsolved")
		channel = ctx.message.channel
		embed, new_channel_name = self.remove_prefix(ctx.message.channel, constants.SOLVED_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="solvedish")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solvedish(self, ctx):
		"""Changes channel name to solvedish-<channel-name>"""
		# log command in console
		print("Received solvedish")
		channel = ctx.message.channel
		embed, new_channel_name = self.add_prefix(ctx.message.channel, constants.SOLVEDISH_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="unsolvedish")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def unsolvedish(self, ctx):
		"""removes solvedish prefix from channel name"""
		# log command in console
		print("Received unsolvedish")
		channel = ctx.message.channel
		embed, new_channel_name = self.remove_prefix(channel, constants.SOLVEDISH_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="backsolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def backsolved(self, ctx):
		"""Changes channel name to backsolved-<channel-name>"""
		# log command in console
		print("Received backsolved")
		channel = ctx.message.channel
		embed, new_channel_name = self.add_prefix(channel, constants.BACKSOLVED_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="unbacksolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def unbacksolved(self, ctx):
		"""removes backsolved prefix from channel name"""
		# log command in console
		print("Received unbacksolved")
		channel = ctx.message.channel
		embed, new_channel_name = self.remove_prefix(channel, constants.BACKSOLVED_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(SolvedCog(bot))
