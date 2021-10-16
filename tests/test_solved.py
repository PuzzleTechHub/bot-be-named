import pytest
from dotenv import load_dotenv
load_dotenv(override=True)
from modules.solved import solved_constants
from modules.solved.cog import SolvedCog


class MockChannel:
    """Class to Mock a Discord Channel"""
    def __init__(self, name):
        self.name = name
        self.mention = '#' + name

    def __repr__(self):
        return self.name


@pytest.mark.parametrize("original_name,prefix,new_name",
                          [("puzzle1", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle1"),
                          ("puzzle1", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle1"),
                          ("puzzle1", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle1"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVED_PREFIX, None),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVEDISH_PREFIX, None),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.BACKSOLVED_PREFIX, None),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle4")])
def test_add_prefix(original_name, prefix, new_name):
    """Ensure prefix gets added if it does not exist, otherwise return original channel name"""
    solved_cog = SolvedCog(None)
    channel = MockChannel(original_name)
    proposed_new_channel = solved_cog.add_prefix(channel, prefix)
    assert proposed_new_channel == new_name



@pytest.mark.parametrize("original_name,prefix,new_name",
                          [("puzzle1", solved_constants.SOLVED_PREFIX, None),
                          ("puzzle1", solved_constants.BACKSOLVED_PREFIX, None),
                          ("puzzle1", solved_constants.SOLVEDISH_PREFIX, None),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVED_PREFIX, f"puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.BACKSOLVED_PREFIX, None),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVEDISH_PREFIX, None),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVED_PREFIX, None),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.BACKSOLVED_PREFIX, None),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVEDISH_PREFIX, f"puzzle3"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVED_PREFIX, None),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.BACKSOLVED_PREFIX, f"puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVEDISH_PREFIX, None)])
def test_remove_prefix(original_name, prefix, new_name):
    """Ensure prefix gets removed if it exists, otherwise return none"""
    solved_cog = SolvedCog(None)
    channel = MockChannel(original_name)
    proposed_new_channel = solved_cog.remove_prefix(channel, prefix)
    assert proposed_new_channel == new_name