from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.main import (
    _handle_investment_bank,
    _handle_phone_search,
    _handle_simple_search,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Дата операции": ["31.12.2021 16:44:00"],
            "Сумма операции": [-1712.0],
            "Категория": ["Супермаркеты"],
            "Описание": ["Я МТС +7 921 11-22-33"],
        }
    )


class TestHandlers:

    @patch("builtins.input", side_effect=["2021-12", "50"])
    def test_handle_investment_bank(
        self,
        mock_input: MagicMock,
        sample_df: pd.DataFrame,
        capsys: pytest.CaptureFixture,
    ) -> None:
        _handle_investment_bank(sample_df)
        captured = capsys.readouterr()
        assert "Сумма, которую удалось бы отложить" in captured.out

    @patch("builtins.input", return_value="МТС")
    def test_handle_simple_search(
        self,
        mock_input: MagicMock,
        sample_df: pd.DataFrame,
        capsys: pytest.CaptureFixture,
    ) -> None:
        _handle_simple_search(sample_df)
        captured = capsys.readouterr()
        assert "Найдено транзакций" in captured.out

    def test_handle_phone_search(
        self, sample_df: pd.DataFrame, capsys: pytest.CaptureFixture
    ) -> None:
        _handle_phone_search(sample_df)
        captured = capsys.readouterr()
        assert "Найдено транзакций с телефонами" in captured.out
