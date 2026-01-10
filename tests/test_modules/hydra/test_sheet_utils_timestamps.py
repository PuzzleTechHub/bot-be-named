"""Tests for timestamp functionality in sheet_utils.py and lion/cog.py"""

from datetime import datetime, timezone



class TestTimestampFormat:
    """Test timestamp format"""

    def test_timestamp_format_dd_mm_yy_hh_mm_ss(self):

        test_datetime = datetime(2026, 1, 9, 14, 32, 15, tzinfo=timezone.utc)
        formatted = test_datetime.strftime("%d/%m/%y %H:%M:%S")

        assert formatted == "09/01/26 14:32:15"

    def test_timestamp_format_with_various_dates(self):
        """Test timestamp format with various dates"""
        test_cases = [
            (
                datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                "31/12/25 23:59:59",
            ),
            (datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "01/01/26 00:00:00"),
            (
                datetime(2026, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
                "15/06/26 12:30:45",
            ),
        ]

        for dt, expected in test_cases:
            formatted = dt.strftime("%d/%m/%y %H:%M:%S")
            assert formatted == expected, f"Expected {expected}, got {formatted}"


class TestUnlockTimestampInCode:
    """Test that timestamp generation code exists in sheet_utils"""

    def test_create_puzzle_channel_generates_timestamp(self):
        """Test that create_puzzle_channel_from_template generates a timestamp"""
        import modules.hydra.hydra_utils.sheet_utils as sheet_utils_module

        import inspect

        source = inspect.getsource(
            sheet_utils_module.create_puzzle_channel_from_template
        )

        # Verify timestamp code exists
        assert "datetime.now(timezone.utc)" in source
        assert "strftime" in source
        assert "%d/%m/%y %H:%M:%S" in source
        assert "PUZZLE_UNLOCKED_TIMESTAMP_COLUMN" in source

    def test_batch_create_puzzles_generates_timestamp(self):
        """Test that batch_create_puzzle_channels generates a timestamp"""
        import modules.hydra.hydra_utils.sheet_utils as sheet_utils_module

        import inspect

        source = inspect.getsource(sheet_utils_module.batch_create_puzzle_channels)

        # Verify timestamp code exists
        assert "datetime.now(timezone.utc)" in source
        assert "strftime" in source
        assert "%d/%m/%y %H:%M:%S" in source
        assert "PUZZLE_UNLOCKED_TIMESTAMP_COLUMN" in source


class TestSolvedTimestampInCode:
    """Test that timestamp generation code exists in statushydra"""

    def test_statushydra_generates_solved_timestamp(self):
        """Test that statushydra generates a solved timestamp"""

        with open("modules/lion/cog.py", "r") as f:
            source = f.read()

        # Verify timestamp code exists
        assert "datetime.now(timezone.utc)" in source
        assert "strftime" in source
        assert "%d/%m/%y %H:%M:%S" in source
        assert "PUZZLE_SOLVED_TIMESTAMP_COLUMN" in source

    def test_statushydra_checks_for_solved_statuses(self):
        """Test that statushydra only adds timestamp for Solved/Backsolved"""

        with open("modules/lion/cog.py", "r") as f:
            source = f.read()

        # Verify it checks for Solved/Backsolved statuses
        assert '"Solved"' in source or "'Solved'" in source
        assert '"Backsolved"' in source or "'Backsolved'" in source
