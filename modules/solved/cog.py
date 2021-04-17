import constants
from discord.ext import commands
from modules.solved.prefix import Prefix
from modules.solved import solved_constants
from utils import discord_utils


# TODO: It's awkward but right now the solved constants have a hyphen at the end
# Which is why we have [:-1] for all the prefixes. We don't want to have that prefix
# Sent to the users, but we do need it for prepending to the channel.
# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class SolvedCog(commands.Cog):
	"""Checks for `solved` and `unsolved` command
	Toggles `solved-` prefix on channel name"""
	def __init__(self, bot):
		self.bot = bot

	def add_prefix(self, channel, prefix: str):
		"""Adds prefix to channel name"""
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = None
		# check if already solved
		if not p.has_prefix():
			# Abusing p notation here
			# Remove other prefixes that might be present
			# e.g. ~backsolved on solved-channel should remove solved- and add backsolved-
			for other_prefix in [op for op in solved_constants.PREFIXES if op != prefix]:
				p = Prefix(channel, other_prefix)
				if p.has_prefix():
					new_channel_name = p.remove_prefix()
			if new_channel_name is None:
				p = Prefix(channel, prefix)
			else:
				p = Prefix(new_channel_name, prefix)
			new_channel_name = p.add_prefix()
		return new_channel_name

	def remove_prefix(self, channel, prefix: str) -> str:
		"""Remove prefix from channel name"""
		# create prefix checking object
		p = Prefix(channel, prefix)
		new_channel_name = None
		# check if already solved
		if p.has_prefix():
			# edit channel name to remove prefix
			new_channel_name = p.remove_prefix()
		return new_channel_name

	@commands.command(name="solved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solved(self, ctx: commands.Context):
		"""Changes channel name to solved-<channel-name>

		Usage: ~solved"""
		# log command in console
		print("Received solved")
		channel = ctx.message.channel
		embed = discord_utils.create_embed()
		new_channel_name = self.add_prefix(channel, solved_constants.SOLVED_PREFIX)
		if new_channel_name:
			await channel.edit(name=new_channel_name)
			embed.add_field(name=f"{constants.SUCCESS}!",
							value=f"Marking {channel.mention} as {solved_constants.SOLVED_PREFIX[:-1]}!",
							inline=False)
		else:
			embed.add_field(name=f"{constants.FAILED}!",
							value=f"Channel already marked as {solved_constants.SOLVED_PREFIX[:-1]}!",
							inline=False)
		await ctx.send(embed=embed)

	@commands.command(name="solvedish")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def solvedish(self, ctx: commands.Context):
		"""Changes channel name to solvedish-<channel-name>

		Usage: ~solvedish"""
		# log command in console
		print("Received solvedish")
		channel = ctx.message.channel
		embed = discord_utils.create_embed()
		new_channel_name = self.add_prefix(ctx.message.channel, solved_constants.SOLVEDISH_PREFIX)
		if new_channel_name:
			await channel.edit(name=new_channel_name)
			embed.add_field(name=f"{constants.SUCCESS}!",
							value=f"Marking {channel.mention} as {solved_constants.SOLVEDISH_PREFIX[:-1]}!",
							inline=False)
		else:
			embed.add_field(name=f"{constants.FAILED}!",
							value=f"Channel already marked as {solved_constants.SOLVEDISH_PREFIX[:-1]}!",
							inline=False)
		await channel.edit(name=new_channel_name)
		await ctx.send(embed=embed)

	@commands.command(name="backsolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def backsolved(self, ctx: commands.Context):
		"""Changes channel name to backsolved-<channel-name>

		Usage: ~backsolved"""
		# log command in console
		print("Received backsolved")
		channel = ctx.message.channel
		embed = discord_utils.create_embed()
		new_channel_name = self.add_prefix(channel, solved_constants.BACKSOLVED_PREFIX)
		if new_channel_name:
			await channel.edit(name=new_channel_name)
			embed.add_field(name=f"{constants.SUCCESS}",
							value=f"Marking {channel.mention} as {solved_constants.BACKSOLVED_PREFIX[:-1]}!",
							inline=False)
		else:
			embed.add_field(name=f"{constants.FAILED}",
							value=f"Channel already marked as {solved_constants.BACKSOLVED_PREFIX[:-1]}!",
							inline=False)
		await ctx.send(embed=embed)

	@commands.command(name="unsolved")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
	)
	async def unsolved(self, ctx: commands.context):
		"""removes one of the solved prefixes from channel name

		Usage: ~unsolved"""
		# log command in console
		print("Received unsolved")
		channel = ctx.message.channel
		embed = discord_utils.create_embed()
		for prefix in solved_constants.PREFIXES:
			new_channel_name = self.remove_prefix(ctx.message.channel, prefix)
			if new_channel_name:
				await channel.edit(name=new_channel_name)
				embed.add_field(name=f"{constants.SUCCESS}!",
								value=f"Marking {channel.mention} as un{prefix[:-1]}!",
								inline=False)
				await ctx.send(embed=embed)
				return
		embed.add_field(name=f"{constants.FAILED}!",
						value=f"Channel is not marked as {solved_constants.SOLVED_PREFIX[:-1]}!",
						inline=False)
		await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(SolvedCog(bot))
