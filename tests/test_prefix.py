import pytest
from modules.solved.prefix import Prefix
from modules.solved import solved_constants


@pytest.mark.parametrize("channel,prefix,has_prefix",
                         [("help", solved_constants.SOLVED_PREFIX, False),
                          ("help", solved_constants.BACKSOLVED_PREFIX, False),
                          ("help", solved_constants.SOLVEDISH_PREFIX, False),
                          (f"{solved_constants.SOLVED_PREFIX}-help", solved_constants.SOLVED_PREFIX, True),
                          (f"{solved_constants.SOLVED_PREFIX}-help", solved_constants.BACKSOLVED_PREFIX, False),
                          (f"{solved_constants.SOLVED_PREFIX}-help", solved_constants.SOLVEDISH_PREFIX, False),
                          (f"{solved_constants.SOLVED_PREFIX}-{solved_constants.BACKSOLVED_PREFIX}-puzzle-2a", solved_constants.SOLVED_PREFIX, True),
                          (f"{solved_constants.SOLVED_PREFIX}-{solved_constants.BACKSOLVED_PREFIX}-puzzle-2a", solved_constants.BACKSOLVED_PREFIX, False),
                          (f"{solved_constants.SOLVED_PREFIX}-{solved_constants.SOLVEDISH_PREFIX}-puzzle-2a", solved_constants.SOLVEDISH_PREFIX, False),
                          (f"{solved_constants.SOLVEDISH_PREFIX}-{solved_constants.SOLVED_PREFIX}-puzzle", solved_constants.SOLVED_PREFIX, False),
                          (f"{solved_constants.SOLVEDISH_PREFIX}-{solved_constants.SOLVED_PREFIX}-puzzle", solved_constants.BACKSOLVED_PREFIX, False),
                          (f"{solved_constants.SOLVEDISH_PREFIX}-{solved_constants.SOLVED_PREFIX}-puzzle", solved_constants.SOLVEDISH_PREFIX, True),
                          (f"{solved_constants.BACKSOLVED_PREFIX}-{solved_constants.SOLVEDISH_PREFIX}-hunt", solved_constants.SOLVED_PREFIX, False),
                          (f"{solved_constants.BACKSOLVED_PREFIX}-{solved_constants.SOLVEDISH_PREFIX}-hunt", solved_constants.BACKSOLVED_PREFIX, True),
                          (f"{solved_constants.BACKSOLVED_PREFIX}-{solved_constants.SOLVEDISH_PREFIX}-hunt", solved_constants.SOLVEDISH_PREFIX, False)])
def test_has_prefix(channel, prefix, has_prefix):
    prefix = Prefix(channel, prefix)
    assert has_prefix == prefix.has_prefix()


@pytest.mark.parametrize("channel,prefix,new_channel",
                         [("help", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}help"),
                          ("puzzle1", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle1"),
                          ("puzzle1", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle1"),
                          ("puzzle1", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle1"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}puzzle2", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}puzzle3", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle3"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}{solved_constants.BACKSOLVED_PREFIX}puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.BACKSOLVED_PREFIX}puzzle4")])
def test_add_prefix(channel, prefix, new_channel):
    prefix = Prefix(channel, prefix)
    if not prefix.has_prefix():
        assert new_channel == prefix.add_prefix()



@pytest.mark.parametrize("channel,prefix,new_channel",
                         [("help", solved_constants.SOLVED_PREFIX, f"help"),
                          ("puzzle1", solved_constants.SOLVED_PREFIX, f"puzzle1"),
                          ("puzzle1", solved_constants.BACKSOLVED_PREFIX, f"puzzle1"),
                          ("puzzle1", solved_constants.SOLVEDISH_PREFIX, f"puzzle1"),
                          (f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle2", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle2", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle2", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVED_PREFIX}{solved_constants.SOLVEDISH_PREFIX}puzzle2"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle3", solved_constants.SOLVED_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle3", solved_constants.BACKSOLVED_PREFIX, f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle3"),
                          (f"{solved_constants.SOLVEDISH_PREFIX}{solved_constants.SOLVED_PREFIX}puzzle3", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.SOLVED_PREFIX}puzzle3"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVED_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.BACKSOLVED_PREFIX, f"puzzle4"),
                          (f"{solved_constants.BACKSOLVED_PREFIX}puzzle4", solved_constants.SOLVEDISH_PREFIX, f"{solved_constants.BACKSOLVED_PREFIX}puzzle4")])
def test_add_prefix(channel, prefix, new_channel):
    prefix = Prefix(channel, prefix)
    if prefix.has_prefix():
        assert new_channel == prefix.remove_prefix()
