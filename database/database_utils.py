from typing import Optional

from sqlalchemy.orm import Session
from database import models

# These are in-memory caches which will be filled by load_all(). Importing this package doesn't touch the database.
PREFIXES: dict = {}
VERIFIEDS: dict = {}
TRUSTEDS: dict = {}
SOLVERS: dict = {}
TESTERS: dict = {}
CUSTOM_COMMANDS: dict = {}
CHANNEL_MIRRORS: dict = {}


def get_prefixes():
    prefixes = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Prefixes).all()
        for row in result:
            prefixes[row.server_id] = row.prefix
    return prefixes


def get_solvers():
    solvers = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Solver").all()
        for row in result:
            if row.server_id in solvers:
                solvers[row.server_id].append(row.role_id)
            else:
                solvers[row.server_id] = [row.role_id]
    return solvers


def get_testers():
    testers = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Tester").all()
        for row in result:
            if row.server_id in testers:
                testers[row.server_id].append(row.role_id)
            else:
                testers[row.server_id] = [row.role_id]
    return testers


def get_verifieds():
    verifieds = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Verified").all()
        for row in result:
            if row.server_id in verifieds:
                verifieds[row.server_id].append(row.role_id)
            else:
                verifieds[row.server_id] = [row.role_id]
    return verifieds


def get_trusteds():
    trusteds = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.Verifieds).filter_by(permissions="Trusted").all()
        for row in result:
            if row.server_id in trusteds:
                trusteds[row.server_id].append(row.role_id)
            else:
                trusteds[row.server_id] = [row.role_id]
    return trusteds


def get_custom_commands():
    custom_commands = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.CustomCommands).all()
        for row in result:
            if row.server_id not in custom_commands:
                custom_commands[row.server_id] = {}
            custom_commands[row.server_id][row.command_name.lower()] = (
                row.command_return,
                row.image,
                row.responses,
            )
    return custom_commands


def get_channel_mirrors():
    channel_mirrors = {}
    with Session(models.DATABASE_ENGINE) as session:
        result = session.query(models.ChannelMirrors).all()
        for row in result:
            if row.source_channel_id not in channel_mirrors:
                channel_mirrors[row.source_channel_id] = set()
            channel_mirrors[row.source_channel_id].add(row.target_channel_id)
    return channel_mirrors


#################
# SHEET TETHERS #
#################


def get_tether(channel_or_cat_id: Optional[int]) -> Optional[models.SheetTethers]:
    """The tether row for a category, channel or thread ID, or None."""
    if channel_or_cat_id is None:
        return None
    with Session(models.DATABASE_ENGINE) as session:
        return session.get(models.SheetTethers, channel_or_cat_id)


def get_all_tethers() -> list[models.SheetTethers]:
    with Session(models.DATABASE_ENGINE) as session:
        return session.query(models.SheetTethers).all()


def set_tether(
    server_id: int,
    server_name: str,
    channel_or_cat_id: int,
    channel_or_cat_name: str,
    sheet_link: str,
):
    """Tethers a category, channel or thread to a sheet. An existing tether only gets the new link."""
    with Session(models.DATABASE_ENGINE) as session:
        result = session.get(models.SheetTethers, channel_or_cat_id)
        if result is not None:
            result.sheet_link = sheet_link
        else:
            session.add(
                models.SheetTethers(
                    server_id=server_id,
                    server_name=server_name,
                    channel_or_cat_id=channel_or_cat_id,
                    channel_or_cat_name=channel_or_cat_name,
                    sheet_link=sheet_link,
                )
            )
        session.commit()


def delete_tether(channel_or_cat_id: int):
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.SheetTethers).filter_by(
            channel_or_cat_id=channel_or_cat_id
        ).delete()
        session.commit()


##################
# SUMMARY GRANTS #
##################


def _grant_id(channel_id: int, role_id: int) -> str:
    """summary_grants' primary key: "<channel id>_<role id>"."""
    return f"{channel_id}_{role_id}"


def add_summary_grant(
    server_id: int,
    server_name: str,
    channel_id: int,
    channel_name: str,
    role_id: int,
    role_name: str,
) -> bool:
    """Lets a role run summaries in a channel. False if it already could."""
    grant_id = _grant_id(channel_id, role_id)
    with Session(models.DATABASE_ENGINE) as session:
        if session.get(models.SummaryGrants, grant_id) is not None:
            return False
        session.add(
            models.SummaryGrants(
                server_id=server_id,
                server_name=server_name,
                channel_id=channel_id,
                channel_name=channel_name,
                role_id=role_id,
                role_name=role_name,
                channel_id_role_id=grant_id,
            )
        )
        session.commit()
    return True


def delete_summary_grant(channel_id: int, role_id: int) -> bool:
    """False if there was no such grant."""
    with Session(models.DATABASE_ENGINE) as session:
        deleted = (
            session.query(models.SummaryGrants)
            .filter_by(channel_id_role_id=_grant_id(channel_id, role_id))
            .delete()
        )
        session.commit()
    return bool(deleted)


def get_server_summary_grants(server_id: int) -> list[models.SummaryGrants]:
    with Session(models.DATABASE_ENGINE) as session:
        return session.query(models.SummaryGrants).filter_by(server_id=server_id).all()


def get_summary_role_ids(channel_id: int) -> list[int]:
    """IDs of the roles allowed to run summaries in a channel."""
    with Session(models.DATABASE_ENGINE) as session:
        rows = session.query(models.SummaryGrants).filter_by(channel_id=channel_id)
        return [row.role_id for row in rows]


def delete_role_summary_grants(role_id: int):
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.SummaryGrants).filter_by(role_id=role_id).delete()
        session.commit()


def delete_channel_summary_grants(channel_id: int):
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.SummaryGrants).filter_by(channel_id=channel_id).delete()
        session.commit()


#################
# SOLVE STREAMS #
#################


def get_solve_streams(sheet_key: str, server_id: int) -> list[models.SolveStreams]:
    """The channels a sheet's solves are posted to in a server."""
    with Session(models.DATABASE_ENGINE) as session:
        return (
            session.query(models.SolveStreams)
            .filter_by(sheet_key=sheet_key, server_id=server_id)
            .all()
        )


def set_solve_stream(
    server_id: int,
    server_name: str,
    channel_id: int,
    channel_name: str,
    sheet_key: str,
) -> bool:
    """Posts a sheet's solves to a channel. Replaces any existing row for the pair, so the names
    are refreshed. True if the pair already existed."""
    with Session(models.DATABASE_ENGINE) as session:
        existed = (
            session.query(models.SolveStreams)
            .filter_by(sheet_key=sheet_key, channel_id=channel_id)
            .delete()
        )
        session.add(
            models.SolveStreams(
                server_id=server_id,
                server_name=server_name,
                channel_id=channel_id,
                channel_name=channel_name,
                sheet_key=sheet_key,
            )
        )
        session.commit()
    return bool(existed)


def delete_solve_stream(sheet_key: str, channel_id: int) -> bool:
    """False if the sheet wasn't posting to that channel."""
    with Session(models.DATABASE_ENGINE) as session:
        deleted = (
            session.query(models.SolveStreams)
            .filter_by(sheet_key=sheet_key, channel_id=channel_id)
            .delete()
        )
        session.commit()
    return bool(deleted)


def delete_channel_solve_streams(channel_id: int):
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.SolveStreams).filter_by(channel_id=channel_id).delete()
        session.commit()


###################
# CHANNEL MIRRORS #
###################
# These also keep the CHANNEL_MIRRORS cache (source id -> set of target ids) in step.


def add_channel_mirror(
    server_id: int,
    server_name: str,
    source_id: int,
    source_name: str,
    target_id: int,
    target_name: str,
) -> bool:
    """Mirrors messages from source into target. False if that mirror already existed."""
    with Session(models.DATABASE_ENGINE) as session:
        existed = session.get(models.ChannelMirrors, (source_id, target_id))
        if existed is None:
            session.add(
                models.ChannelMirrors(
                    server_id=server_id,
                    server_name=server_name,
                    source_channel_id=source_id,
                    source_channel_name=source_name,
                    target_channel_id=target_id,
                    target_channel_name=target_name,
                )
            )
            session.commit()
    CHANNEL_MIRRORS.setdefault(source_id, set()).add(target_id)
    return existed is None


def delete_channel_mirror(source_id: int, target_id: int) -> bool:
    """False if there was no such mirror."""
    with Session(models.DATABASE_ENGINE) as session:
        deleted = (
            session.query(models.ChannelMirrors)
            .filter_by(source_channel_id=source_id, target_channel_id=target_id)
            .delete()
        )
        session.commit()
    if source_id in CHANNEL_MIRRORS:
        CHANNEL_MIRRORS[source_id].discard(target_id)
    return bool(deleted)


def get_server_channel_mirrors(server_id: int) -> list[models.ChannelMirrors]:
    with Session(models.DATABASE_ENGINE) as session:
        return session.query(models.ChannelMirrors).filter_by(server_id=server_id).all()


def delete_channel_mirrors_for(channel_id: int):
    """Deletes every mirror from or into a channel, e.g. when it's deleted."""
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.ChannelMirrors).filter_by(
            source_channel_id=channel_id
        ).delete()
        session.query(models.ChannelMirrors).filter_by(
            target_channel_id=channel_id
        ).delete()
        session.commit()
    CHANNEL_MIRRORS.pop(channel_id, None)
    for target_ids in CHANNEL_MIRRORS.values():
        target_ids.discard(channel_id)
