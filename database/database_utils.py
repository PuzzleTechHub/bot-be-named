from sqlalchemy.orm import Session

import constants
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
            custom_commands[row.server_id][row.command_name.lower()] = _command_entry(
                row
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


def get_tether(channel_or_cat_id: int | None) -> models.SheetTethers | None:
    """The tether row for a category, channel or thread ID, or None."""
    if channel_or_cat_id is None:
        return None
    with Session(models.DATABASE_ENGINE) as session:
        return session.get(models.SheetTethers, channel_or_cat_id)


def get_tethers(ids) -> dict[int, models.SheetTethers]:
    """The tether rows for many category, channel or thread IDs in one query, keyed by ID.
    IDs with no tether, and None, are left out."""
    wanted = {
        channel_or_cat_id for channel_or_cat_id in ids if channel_or_cat_id is not None
    }
    if not wanted:
        return {}
    with Session(models.DATABASE_ENGINE) as session:
        rows = (
            session.query(models.SheetTethers)
            .filter(models.SheetTethers.channel_or_cat_id.in_(wanted))
            .all()
        )
    return {row.channel_or_cat_id: row for row in rows}


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


############
# PREFIXES #
############


def add_server(server_id: int, server_name: str):
    """Gives a server the default prefix if it has none, plus empty role and custom command
    caches."""
    if server_id not in PREFIXES:
        with Session(models.DATABASE_ENGINE) as session:
            row = session.get(models.Prefixes, server_id)
            if row is None:
                session.add(
                    models.Prefixes(
                        server_id=server_id,
                        server_name=server_name,
                        prefix=constants.DEFAULT_BOT_PREFIX,
                    )
                )
                session.commit()
                PREFIXES[server_id] = constants.DEFAULT_BOT_PREFIX
            else:
                PREFIXES[server_id] = row.prefix
    for cache in PERMISSION_CACHES.values():
        cache.setdefault(server_id, [])
    CUSTOM_COMMANDS.setdefault(server_id, {})


def set_prefix(server_id: int, prefix: str):
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.Prefixes).filter_by(server_id=server_id).update(
            {"prefix": prefix}
        )
        session.commit()
    PREFIXES[server_id] = prefix


def get_server_prefix(server_id: int) -> str:
    """The prefix in the database, or the default one if the server has none."""
    with Session(models.DATABASE_ENGINE) as session:
        row = session.get(models.Prefixes, server_id)
    return row.prefix if row is not None else constants.DEFAULT_BOT_PREFIX


#############
# VERIFIEDS #
#############
# These also keep the VERIFIEDS / TRUSTEDS / SOLVERS / TESTERS caches (server id -> role ids) in step.

PERMISSION_CACHES = {
    models.VERIFIED: VERIFIEDS,
    models.TRUSTED: TRUSTEDS,
    models.SOLVER: SOLVERS,
    models.TESTER: TESTERS,
}


def _role_id_permissions(role_id: int, permissions: str) -> str:
    """verifieds' primary key: "<role id>_<permissions>"."""
    return f"{role_id}_{permissions}"


def add_permission_role(
    server_id: int,
    server_name: str,
    role_id: int,
    role_name: str,
    permissions: str,
) -> bool:
    """Puts a role in a permission category. False if it was already in it."""
    key = _role_id_permissions(role_id, permissions)
    with Session(models.DATABASE_ENGINE) as session:
        if session.get(models.Verifieds, key) is not None:
            return False
        session.add(
            models.Verifieds(
                server_id=server_id,
                server_name=server_name,
                role_id=role_id,
                role_name=role_name,
                permissions=permissions,
                role_id_permissions=key,
            )
        )
        session.commit()
    PERMISSION_CACHES[permissions].setdefault(server_id, []).append(role_id)
    return True


def delete_permission_role(server_id: int, role_id: int, permissions: str) -> bool:
    """False if the role wasn't in that category in this server."""
    with Session(models.DATABASE_ENGINE) as session:
        deleted = (
            session.query(models.Verifieds)
            .filter_by(
                server_id=server_id,
                role_id_permissions=_role_id_permissions(role_id, permissions),
            )
            .delete()
        )
        session.commit()
    role_ids = PERMISSION_CACHES[permissions].get(server_id, [])
    if role_id in role_ids:
        role_ids.remove(role_id)
    return bool(deleted)


def get_server_permission_roles(server_id: int) -> dict[str, list[int]]:
    """Role IDs in each permission category, for every category."""
    role_ids: dict[str, list[int]] = {
        permissions: [] for permissions in models.VERIFIED_CATEGORIES
    }
    with Session(models.DATABASE_ENGINE) as session:
        for row in session.query(models.Verifieds).filter_by(server_id=server_id):
            if row.permissions in role_ids:
                role_ids[row.permissions].append(row.role_id)
    return role_ids


###################
# CUSTOM COMMANDS #
###################
# Server IDs here can also be constants.DB_GLOBAL, for global commands. These keep the
# CUSTOM_COMMANDS cache (server id -> command name -> entry) in step. An entry is
# (command_return, is_image, responses). TODO: make it a class


def _command_key(server_id: int, command_name: str) -> str:
    """custom_commands' primary key: "<server id> <command name>"."""
    return f"{server_id} {command_name}"


def _command_entry(row: models.CustomCommands) -> tuple:
    return (row.command_return, row.image, row.responses)


def find_custom_command(server_id: int, command_name: str) -> tuple | None:
    """Looks a command up in the database, in this server and then globally, and caches it under
    the ID it was found under. None if it's in neither."""
    with Session(models.DATABASE_ENGINE) as session:
        for owner_id in (server_id, constants.DB_GLOBAL):
            row = session.get(
                models.CustomCommands, _command_key(owner_id, command_name)
            )
            if row is not None:
                entry = _command_entry(row)
                CUSTOM_COMMANDS.setdefault(owner_id, {})[command_name] = entry
                return entry
    return None


def add_custom_command(
    server_id: int,
    server_name: str,
    command_name: str,
    responses: list[str],
    is_image: bool,
) -> bool:
    """Adds a command. False if the database already had one by that name, which then gets cached."""
    key = _command_key(server_id, command_name)
    with Session(models.DATABASE_ENGINE) as session:
        row = session.get(models.CustomCommands, key)
        if row is not None:
            CUSTOM_COMMANDS.setdefault(server_id, {})[command_name] = _command_entry(
                row
            )
            return False
        session.add(
            models.CustomCommands(
                server_id=server_id,
                server_name=server_name,
                server_id_command=key,
                command_name=command_name,
                command_return=responses[0],  # TODO Drop this soon
                image=is_image,
                responses=responses,
            )
        )
        session.commit()
    CUSTOM_COMMANDS.setdefault(server_id, {})[command_name] = (
        responses[0],
        is_image,
        responses,
    )
    return True


def set_custom_command_responses(
    server_id: int, command_name: str, responses: list[str]
):
    """Replaces a command's responses. Whether it's an image is kept."""
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.CustomCommands).filter_by(
            server_id_command=_command_key(server_id, command_name)
        ).update({"command_return": responses[0], "responses": responses})
        session.commit()
    server_commands = CUSTOM_COMMANDS.setdefault(server_id, {})
    old = server_commands.get(command_name)
    is_image = old[1] if old is not None else False
    server_commands[command_name] = (responses[0], is_image, responses)


def delete_custom_command(server_id: int, command_name: str):
    CUSTOM_COMMANDS.get(server_id, {}).pop(command_name, None)
    with Session(models.DATABASE_ENGINE) as session:
        session.query(models.CustomCommands).filter_by(
            server_id_command=_command_key(server_id, command_name)
        ).delete()
        session.commit()


def get_server_custom_commands(server_id: int) -> dict[str, tuple]:
    """Command name -> entry, for one server (or constants.DB_GLOBAL)."""
    with Session(models.DATABASE_ENGINE) as session:
        rows = session.query(models.CustomCommands).filter_by(server_id=server_id)
        return {row.command_name.lower(): _command_entry(row) for row in rows}


###############
# SERVER DATA #
###############


def delete_server_data(server_id: int):
    """Deletes everything stored for a server, e.g. when the bot leaves it, cache entries too."""
    with Session(models.DATABASE_ENGINE) as session:
        mirrors = (
            session.query(models.ChannelMirrors).filter_by(server_id=server_id).all()
        )
        for table in (
            models.CustomCommands,
            models.Prefixes,
            models.Verifieds,
            models.SheetTethers,
            models.SummaryGrants,
            models.SolveStreams,
            models.ChannelMirrors,
        ):
            session.query(table).filter_by(server_id=server_id).delete()
        session.commit()
    for cache in (PREFIXES, CUSTOM_COMMANDS, *PERMISSION_CACHES.values()):
        cache.pop(server_id, None)
    for mirror in mirrors:
        CHANNEL_MIRRORS.get(mirror.source_channel_id, set()).discard(
            mirror.target_channel_id
        )
