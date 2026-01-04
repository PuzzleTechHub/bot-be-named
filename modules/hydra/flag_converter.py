from nextcord.ext import commands
from typing import Optional

class chanhydra(commands.FlagConverter, delimiter=": ", prefix=""):
    puzzle_name: str
    template_name: str = ""
    puzzle_url: Optional[str]
