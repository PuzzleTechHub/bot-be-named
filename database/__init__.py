# ruff: noqa: F401

from database.database_utils import (
    CHANNEL_MIRRORS,
    CUSTOM_COMMANDS,
    PERMISSION_CACHES,
    PREFIXES,
    SOLVERS,
    TESTERS,
    TRUSTEDS,
    VERIFIEDS,
    add_channel_mirror,
    add_custom_command,
    add_permission_role,
    add_server,
    add_summary_grant,
    delete_channel_mirror,
    delete_channel_mirrors_for,
    delete_channel_solve_streams,
    delete_channel_summary_grants,
    delete_custom_command,
    delete_permission_role,
    delete_role_summary_grants,
    delete_server_data,
    delete_solve_stream,
    delete_summary_grant,
    delete_tether,
    find_custom_command,
    get_all_tethers,
    get_channel_mirrors,
    get_custom_commands,
    get_prefixes,
    get_server_channel_mirrors,
    get_server_custom_commands,
    get_server_permission_roles,
    get_server_prefix,
    get_server_summary_grants,
    get_solve_streams,
    get_solvers,
    get_summary_role_ids,
    get_testers,
    get_tether,
    get_tethers,
    get_trusteds,
    get_verifieds,
    set_custom_command_responses,
    set_prefix,
    set_solve_stream,
    set_tether,
)
from database.models import (
    DATABASE_ENGINE,
    VERIFIED_CATEGORIES,
    Base,
    ChannelMirrors,
    CustomCommands,
    Prefixes,
    SheetTethers,
    SolveStreams,
    SummaryGrants,
    Verifieds,
)


def load_all():
    """Create any missing tables, then fill every cache from the database.

    The caches are refilled in place, so code holding a reference to one sees the new contents.
    """
    Base.metadata.create_all(DATABASE_ENGINE)
    for cache, loader in (
        (PREFIXES, get_prefixes),
        (VERIFIEDS, get_verifieds),
        (TRUSTEDS, get_trusteds),
        (SOLVERS, get_solvers),
        (TESTERS, get_testers),
        (CUSTOM_COMMANDS, get_custom_commands),
        (CHANNEL_MIRRORS, get_channel_mirrors),
    ):
        fresh = loader()
        cache.clear()
        cache.update(fresh)
