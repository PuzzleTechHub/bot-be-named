from typing import Optional

from sqlalchemy.orm import Session
from database import models


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
