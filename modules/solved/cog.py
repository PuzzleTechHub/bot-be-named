import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
from modules.solved import solved_constants
from utils import discord_utils


# TODO: It's awkward but right now the solved constants have a hyphen at the end
# Which is why we have [:-1] for all the prefixes. We don't want to have that prefix
# Sent to the users, but we do need it for prepending to the channel.
class SolvedCog(commands.Cog):
	"""Checks for `solved` and `unsolved` command
	Toggles `solved-` prefix on channel name"""
	def __init__(self, bot):
		self.bot = bot

	def add_prefix(self, channel, prefix):
		"""Adds prefix to channel name"""
		embed = discord_utils.create_embed()
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = str(channel)
		# check if already solved
		if not p.has_prefix():
			new_channel_name = p.add_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as {prefix[:-1]}!")
		# already solved
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"Channel already marked as {prefix[:-1]}!")
		return embed, new_channel_name

	def remove_prefix(self, channel, prefix):
		"""Remove prefix from channel name"""
		embed = discord_utils.create_embed()
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = None
		# check if already solved
		if p.has_prefix():
			# edit channel name to remove prefix
			new_channel_name = p.remove_prefix()
			embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as {prefix[:-1]}!")
		return new_channel_name

	@commands.command(name="solved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solved(self, ctx):
		"""Changes channel name to solved-<channel-name>"""
		# log command in console
		print("Received solved")
		channel = ctx.message.channel
		embed, new_channel_name = self.add_prefix(channel, solved_constants.SOLVED_PREFIX)
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
		for prefix in solved_constants.PREFIXES:
			new_channel_name = self.remove_prefix(ctx.message.channel, prefix)
			if new_channel_name:
				await channel.edit(name=new_channel_name)
				embed = discord_utils.create_embed()
				embed.add_field(name=f"{constants.SUCCESS}!", value=f"Marking {channel.mention} as un{prefix[:-1]}!")
				await ctx.send(embed=embed)
				return
		embed = discord_utils.create_embed()
		embed.add_field(name=f"{constants.FAILED}!", value=f"Channel is not marked as {solved_constants.SOLVED_PREFIX[:-1]}!")
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
		embed, new_channel_name = self.add_prefix(ctx.message.channel, solved_constants.SOLVEDISH_PREFIX)
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
		embed, new_channel_name = self.add_prefix(channel, solved_constants.BACKSOLVED_PREFIX)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(SolvedCog(bot))
