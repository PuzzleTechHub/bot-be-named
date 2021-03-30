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