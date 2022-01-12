from database.models import (
    DATABASE_ENGINE,
    VERIFIED_CATEGORIES,
    Verifieds,
    CustomCommands,
    Prefixes,
    SheetTethers,
    SheetTemplates,
)

from database.database_utils import (
    get_prefixes,
    get_verifieds,
    get_trusteds,
    get_custom_commands,
)

PREFIXES = get_prefixes()
VERIFIEDS = get_verifieds()
TRUSTEDS = get_trusteds()
CUSTOM_COMMANDS = get_custom_commands()
