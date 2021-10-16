# import pytest
# from dotenv import load_dotenv
# load_dotenv(override=True)
# from modules.cipher_race import cipher_race_utils, cipher_race_constants


# @pytest.mark.parametrize("answer,answer_list,correct",
#                          [("and", ["but", "not", "and"], cipher_race_constants.CORRECT),
#                           ("but", ["but", "not", "and"], cipher_race_constants.CORRECT),
#                           ("not", ["but", "not", "and"], cipher_race_constants.CORRECT),
#                           ("the", ["but", "not", "and"], cipher_race_constants.INCORRECT),
#                           ("it", ["but", "not", "and"], cipher_race_constants.INCORRECT),
#                           ("strength", ["strengthen", "conditioning"], cipher_race_constants.INCORRECT),
#                           ("condition", ["strengthen", "conditioning"], cipher_race_constants.INCORRECT),
#                           ("strengthen", ["strengthen", "conditioning"], cipher_race_constants.CORRECT),
#                           ("conditioning", ["strengthen", "conditioning"], cipher_race_constants.CORRECT)
#                           ])
# def test_get_answer_result(answer, answer_list, correct):
#     result = cipher_race_utils.get_answer_result(answer, answer_list)
#     assert result == correct


# @pytest.mark.parametrize("level,time",
#                          [(1, 60),
#                           (2, 60),
#                           (3, 60),
#                           (4, 60),
#                           (5, 60),
#                           (6, 70),
#                           (7, 70),
#                           (8, 70),
#                           (9, 70),
#                           (10, 70),
#                           (11, 80)])
# def test_compute_level_time(level, time):
#     assert cipher_race_utils.compute_level_time(level) == time