"""
Parameters for custom commands: a reply can hold $1, $2, ... for the words typed after
the command name, and $* for all of them.
"""

import re

# $1 to $99, or $*
PARAMETER_RE = re.compile(r"\$(\d{1,2}|\*)")

# "words in double quotes" (straight or curly, as phones type them), or a plain word.
# Apostrophes and backslashes are left alone, so don't, Pat's and C:\path come through as typed.
ARGUMENT_RE = re.compile(r'["“”]([^"“”]*)["“”]|(\S+)')


def arguments_after_command(content: str, prefix: str) -> list[str]:
    """The words typed after "<prefix><command name>". "Quoted words" count as one."""
    parts = content[len(prefix) :].split(maxsplit=1)
    text = parts[1] if len(parts) > 1 else ""
    return [
        quoted if quoted is not None else word
        for quoted, word in (
            (match.group(1), match.group(2)) for match in ARGUMENT_RE.finditer(text)
        )
    ]


def fill_parameters(reply: str, arguments: list[str]) -> str:
    """Puts the arguments into the reply's $1, $2, ... and $*.

    A placeholder with no matching argument stays as it is, so replies that mention
    prices like "$5" keep working when the command is called without arguments."""

    def replace(match):
        if match.group(1) == "*":
            return " ".join(arguments) if arguments else match.group(0)
        number = int(match.group(1))
        if 1 <= number <= len(arguments):
            return arguments[number - 1]
        return match.group(0)

    return PARAMETER_RE.sub(replace, reply)
