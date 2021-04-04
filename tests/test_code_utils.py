import pytest
from modules.code import code_utils, code_constants


@pytest.mark.parametrize("answer,answer_list,correct",
                         [("and", ["but", "not", "and"], code_constants.CORRECT),
                          ("but", ["but", "not", "and"], code_constants.CORRECT),
                          ("not", ["but", "not", "and"], code_constants.CORRECT),
                          ("the", ["but", "not", "and"], code_constants.INCORRECT),
                          ("it", ["but", "not", "and"], code_constants.INCORRECT),
                          ("strength", ["strengthen", "conditioning"], code_constants.INCORRECT),
                          ("condition", ["strengthen", "conditioning"], code_constants.INCORRECT),
                          ("strengthen", ["strengthen", "conditioning"], code_constants.CORRECT),
                          ("conditioning", ["strengthen", "conditioning"], code_constants.CORRECT)
                          ])
def test_get_answer_result(answer, answer_list, correct):
    result = code_utils.get_answer_result(answer, answer_list)
    assert result == correct


@pytest.mark.parametrize("level,time",
                         [(1, 60),
                          (2, 60),
                          (3, 60),
                          (4, 60),
                          (5, 60),
                          (6, 70),
                          (7, 70),
                          (8, 70),
                          (9, 70),
                          (10, 70),
                          (11, 80)])
def test_compute_level_time(level, time):
    assert code_utils.compute_level_time(level) == time