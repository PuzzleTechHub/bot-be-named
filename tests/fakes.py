"""Small stand-ins for Discord objects, plus helpers to add test database rows.

Permissions use the real nextcord.PermissionOverwrite and messages use the real
nextcord.Embed, so permission logic and embed contents are real. FakeContext.send
refuses embeds that Discord would reject.
"""

import nextcord
from sqlalchemy.orm import Session

import database

SERVER_ID = 1


class FakeRole:
    def __init__(self, role_id: int, name: str):
        self.id = role_id
        self.name = name
        self.mention = f"<@&{role_id}>"

    def is_default(self):
        return self.name == "@everyone"

    def __eq__(self, other):
        return isinstance(other, FakeRole) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"FakeRole({self.name})"


class _HasOverwrites:
    def __init__(self, overwrites=None):
        self.overwrites = dict(overwrites or {})

    def overwrites_for(self, role):
        return self.overwrites.get(role, nextcord.PermissionOverwrite())


class FakeChannel(_HasOverwrites):
    def __init__(self, channel_id, name, category=None, overwrites=None):
        super().__init__(overwrites)
        self.id = channel_id
        self.name = name
        self.mention = f"<#{channel_id}>"
        self.category = category
        self.category_id = category.id if category else None
        if category is not None:
            category.text_channels.append(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"FakeChannel({self.name})"


class FakeCategory(_HasOverwrites):
    def __init__(self, category_id, name, overwrites=None):
        super().__init__(overwrites)
        self.id = category_id
        self.name = name
        self.text_channels = []

    def __repr__(self):
        return f"FakeCategory({self.name})"


class FakeGuild:
    def __init__(self, guild_id=SERVER_ID, name="Test server", roles=(), categories=()):
        self.id = guild_id
        self.name = name
        self.roles = list(roles)
        self.categories = list(categories)

    def get_role(self, role_id):
        return next((role for role in self.roles if role.id == role_id), None)

    def get_channel(self, channel_id):
        for category in self.categories:
            if category.id == channel_id:
                return category
            for channel in category.text_channels:
                if channel.id == channel_id:
                    return channel
        return None


class FakeMember:
    def __init__(self, member_id=1000, name="solver", roles=()):
        self.id = member_id
        self.name = name
        self.roles = list(roles)
        self.bot = False


class FakeMessage:
    def __init__(self, content="", author=None, channel=None, embed=None):
        self.content = content
        self.author = author
        self.channel = channel
        self.guild = None
        self.embed = embed
        self.deleted = False

    async def delete(self):
        if self.deleted:
            raise nextcord.NotFound(_FakeResponse(404), "Unknown Message")  # type: ignore
        self.deleted = True


class _FakeResponse:
    def __init__(self, status):
        self.status = status
        self.reason = "Not Found"


def check_embed(embed: nextcord.Embed):
    """Raise if Discord would reject this embed."""
    if embed.title and len(embed.title) > 256:
        raise ValueError("Embed title over 256 characters")
    if embed.description and len(embed.description) > 4096:
        raise ValueError("Embed description over 4096 characters")
    if len(embed.fields) > 25:
        raise ValueError("Embed has more than 25 fields")
    for field in embed.fields:
        if not field.name or not field.value:
            raise ValueError("Embed field with an empty name or value")
        if len(field.name) > 256:
            raise ValueError("Embed field name over 256 characters")
        if len(field.value) > 1024:
            raise ValueError("Embed field value over 1024 characters")
    if len(embed) > 6000:
        raise ValueError("Embed over 6000 characters in total")


class FakeContext:
    """Records everything sent. ctx.message.channel is ctx.channel, like nextcord."""

    def __init__(self, guild, channel, author=None, content="~command"):
        self.guild = guild
        self.channel = channel
        self.author = author or FakeMember()
        self.message = FakeMessage(content, self.author, channel)
        self.message.guild = guild
        self.sent = []

    async def send(self, content=None, embed=None):
        if embed is not None:
            check_embed(embed)
        message = FakeMessage(content or "", channel=self.channel, embed=embed)
        self.sent.append(message)
        return message

    @property
    def sent_embeds(self):
        return [message.embed for message in self.sent if message.embed is not None]


def add_tether(channel_or_cat_id, sheet_link, server_id=SERVER_ID):
    with Session(database.DATABASE_ENGINE) as session:
        session.add(
            database.SheetTethers(
                server_id=server_id,
                server_name="Test server",
                channel_or_cat_id=channel_or_cat_id,
                channel_or_cat_name="test",
                sheet_link=sheet_link,
            )
        )
        session.commit()


def add_grant(channel, role, server_id=SERVER_ID):
    """Same row ~summaryallowhydra writes."""
    with Session(database.DATABASE_ENGINE) as session:
        session.add(
            database.SummaryGrants(
                server_id=server_id,
                server_name="Test server",
                channel_id=channel.id,
                channel_name=channel.name,
                role_id=role.id,
                role_name=role.name,
                channel_id_role_id=f"{channel.id}_{role.id}",
            )
        )
        session.commit()


class FakeOverviewSheet:
    """Stands in for sheet_utils.OverviewSheet. rows are the Overview tab, row 1 first."""

    def __init__(self, sheet_link, rows):
        self.sheet_url = sheet_link
        self.overview_data = rows
        self.worksheet = f"Overview of {sheet_link}"


def patch_overview_sheets(monkeypatch, sheets):
    """sheets maps a sheet link to its Overview rows, or to an exception to raise.
    Returns the list of links opened, in order."""
    from utils import sheet_utils

    opened = []

    def open_sheet(gspread_client, sheet_link):
        opened.append(sheet_link)
        rows = sheets[sheet_link]
        if isinstance(rows, Exception):
            raise rows
        return FakeOverviewSheet(sheet_link, rows)

    monkeypatch.setattr(sheet_utils, "OverviewSheet", open_sheet)
    return opened
