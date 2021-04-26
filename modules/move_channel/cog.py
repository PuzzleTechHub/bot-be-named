import constants
import discord
from discord.ext import commands
from utils import discord_utils


# Big thanks to denvercoder1 and his professor-vector-discord-bot repo
# https://github.com/DenverCoder1/professor-vector-discord-bot
class MoveChannelCog(commands.Cog, name="Move Channel"):
	"""Checks for `movechannel` command
	Moves current channel to given category"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="movechannel")
	@commands.has_any_role(
		constants.VERIFIED_PUZZLER,
		constants.TA_VERIFIED_PUZZLER_ROLE_ID
	)
	async def movechannel(self, ctx, *args):
		"""Command to move channel to category with given name"""
		print("Received movechannel")
		embed = discord_utils.create_embed()
		# check for category name arguments
		if len(args) > 0:
			# join arguments to form channel name
			category_name = " ".join(args)
			# get current channel
			channel = ctx.channel
			# get new category
			new_category = discord.utils.get(ctx.guild.channels, name=category_name)
			if new_category is not None:
				embed.add_field(name=f"{constants.SUCCESS}!", value=f"Moving {channel.mention} to {new_category}!")
				# reply to user
				await ctx.send(embed=embed)
				# move channel
				await ctx.channel.edit(category=new_category)
			else:
				embed.add_field(name=f"{constants.FAILED}!", value=f"Could not find category `{category_name}`")
				# reply to user
				await ctx.send(embed=embed)
		# no argument passed
		else:
			embed.add_field(name=f"{constants.FAILED}!", value=f"You must specify a category!")
			# reply to user
			await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(MoveChannelCog(bot))
