from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.utils import (
    filter_by_date_range,
    get_greeting,
    read_excel_file,
    read_user_settings,
)


class TestGetGreeting:

    @pytest.mark.parametrize(
        "hour, expected",
        [
            (6, "Доброе утро"),
            (9, "Доброе утро"),
            (11, "Доброе утро"),
            (12, "Добрый день"),
            (15, "Добрый день"),
            (17, "Добрый день"),
            (18, "Добрый вечер"),
            (21, "Добрый вечер"),
            (23, "Доброй ночи"),
            (2, "Доброй ночи"),
            (5, "Доброй ночи"),
        ],
    )
    def test_greeting(self, hour: int, expected: str) -> None:
        time = datetime(2024, 1, 1, hour, 0, 0)
        assert get_greeting(time) == expected


class TestReadExcelFile:

    def test_read_excel_file_success(self, tmp_path: Path) -> None:
        """Создаём тестовый Excel и читаем его."""
        test_file = tmp_path / "test.xlsx"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df.to_excel(test_file, index=False)

        result = read_excel_file(str(test_file))
        assert len(result) == 2
        assert list(result.columns) == ["a", "b"]

    def test_read_excel_file_not_found(self) -> None:
        result = read_excel_file("nonexistent.xlsx")
        assert result.empty


class TestReadUserSettings:

    def test_read_settings_success(self, tmp_path: Path) -> None:
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            '{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}',
            encoding="utf-8",
        )
        result = read_user_settings(str(settings_file))
        assert result["user_currencies"] == ["USD"]
        assert result["user_stocks"] == ["AAPL"]

    def test_read_settings_not_found(self) -> None:
        result = read_user_settings("nonexistent.json")
        assert result == {"user_currencies": [], "user_stocks": []}

    def test_read_settings_invalid_json(self, tmp_path: Path) -> None:
        settings_file = tmp_path / "invalid.json"
        settings_file.write_text("invalid json", encoding="utf-8")
        result = read_user_settings(str(settings_file))
        assert result == {"user_currencies": [], "user_stocks": []}


class TestFilterByDateRange:

    def test_filter_success(self) -> None:
        df = pd.DataFrame(
            {
                "Дата операции": [
                    "01.01.2024 10:00:00",
                    "01.02.2024 10:00:00",
                    "01.03.2024 10:00:00",
                ],
                "Сумма": [100, 200, 300],
            }
        )
        start = datetime(2024, 1, 1)
        end = datetime(2024, 2, 15)

        result = filter_by_date_range(df, start, end)
        assert len(result) == 2
