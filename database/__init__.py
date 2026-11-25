# ruff: noqa: F401

from database.models import (
    DATABASE_ENGINE,
    VERIFIED_CATEGORIES,
    Verifieds,
    CustomCommands,
    Prefixes,
    SheetTethers,
    SummaryGrants,
    SolveStreams,
    ChannelMirrors,
)

from database.database_utils import (
    PREFIXES,
    VERIFIEDS,
    TRUSTEDS,
    SOLVERS,
    TESTERS,
    CUSTOM_COMMANDS,
    CHANNEL_MIRRORS,
    get_prefixes,
    get_verifieds,
    get_trusteds,
    get_solvers,
    get_testers,
    get_custom_commands,
    get_channel_mirrors,
    get_tether,
    get_all_tethers,
    set_tether,
    delete_tether,
    add_summary_grant,
    delete_summary_grant,
    get_server_summary_grants,
    get_summary_role_ids,
    delete_role_summary_grants,
    delete_channel_summary_grants,
    get_solve_streams,
    set_solve_stream,
    delete_solve_stream,
    delete_channel_solve_streams,
    add_channel_mirror,
    delete_channel_mirror,
    get_server_channel_mirrors,
    delete_channel_mirrors_for,
)

from database.models import Base


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
