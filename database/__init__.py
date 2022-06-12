from database.database_utils import (
    get_custom_commands,
    get_prefixes,
    get_solvers,
    get_testers,
    get_trusteds,
    get_verifieds,
)
from database.models import (
    DATABASE_ENGINE,
    VERIFIED_CATEGORIES,
    CustomCommands,
    Prefixes,
    SheetTemplates,
    SheetTethers,
    Verifieds,
)

PREFIXES = get_prefixes()
VERIFIEDS = get_verifieds()
TRUSTEDS = get_trusteds()
SOLVERS = get_solvers()
TESTERS = get_testers()
CUSTOM_COMMANDS = get_custom_commands()
