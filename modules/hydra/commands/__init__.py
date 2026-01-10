"""
Auto-loader for hydra commands.

Each command module should export a setup_cmd(cog) function that registers
the command with the bot. The loader will discover all .py files in this
package and call their setup_cmd functions.
"""

from importlib import import_module
from pathlib import Path


def load_commands(cog):
    """
    Automatically load all command modules in this package.

    Args:
        cog: The HydraCog instance that provides shared resources
             (gspread_client, lock, bot, etc.)
    """
    cmds_dir = Path(__file__).parent

    for module_file in sorted(cmds_dir.glob("*.py")):
        if module_file.name in ("__init__.py",) or module_file.name.startswith("_"):
            continue

        module_name = f"modules.hydra.commands.{module_file.stem}"

        try:
            mod = import_module(module_name)
            if hasattr(mod, "setup_cmd"):
                mod.setup_cmd(cog)
            else:
                cog.bot.logger.warning(
                    f"Command module {module_name} has no setup_cmd function"
                )
        except Exception as e:
            cog.bot.logger.exception(
                f"Failed to load command module {module_name}: {e}"
            )
