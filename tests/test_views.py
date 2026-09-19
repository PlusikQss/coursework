from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.views import (
    get_cards_info,
    get_currency_rates,
    get_stock_prices,
    get_top_transactions,
    main_page,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Тестовый датафрейм с транзакциями."""
    return pd.DataFrame(
        {
            "Дата операции": [
                "01.12.2021 10:00:00",
                "15.12.2021 12:00:00",
                "20.12.2021 14:00:00",
                "25.12.2021 18:00:00",
            ],
            "Номер карты": ["*1234", "*1234", "*5678", "*5678"],
            "Сумма платежа": [-1000.0, -500.0, -2000.0, -300.0],
            "Категория": ["Супермаркеты", "Фастфуд", "ЖКХ", "Транспорт"],
            "Описание": ["Лента", "KFC", "ЖКУ", "Метро"],
        }
    )


class TestGetCurrencyRates:

    @patch("src.views.requests.get")
    def test_get_currency_rates_success(self, mock_get: MagicMock) -> None:
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"rates": {"RUB": 73.21}}
        mock_response.raise_for_status.return_value = None

        with patch("src.views.os.getenv", return_value="test_key"):
            result = get_currency_rates(["USD"])

        assert len(result) == 1
        assert result[0]["currency"] == "USD"
        assert result[0]["rate"] == 73.21

    def test_get_currency_rates_no_api_key(self) -> None:
        with patch("src.views.os.getenv", return_value=None):
            result = get_currency_rates(["USD"])
        assert result == [{"currency": "USD", "rate": 0.0}]

    @patch("src.views.requests.get")
    def test_get_currency_rates_api_error(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = Exception("API error")

        with patch("src.views.os.getenv", return_value="test_key"):
            result = get_currency_rates(["USD"])

        assert result == [{"currency": "USD", "rate": 0.0}]


class TestGetStockPrices:

    @patch("yfinance.Ticker")
    def test_get_stock_prices_success(self, mock_ticker: MagicMock) -> None:
        mock_history = MagicMock()
        mock_history.empty = False
        mock_close = MagicMock()
        mock_close.iloc = MagicMock()
        mock_close.iloc.__getitem__ = MagicMock(return_value=150.12)
        mock_history.__getitem__ = MagicMock(return_value=mock_close)

        mock_ticker.return_value.history.return_value = mock_history

        result = get_stock_prices(["AAPL"])

        assert len(result) == 1
        assert result[0]["stock"] == "AAPL"
        assert result[0]["price"] == 150.12

    @patch("yfinance.Ticker")
    def test_get_stock_prices_empty(self, mock_ticker: MagicMock) -> None:
        mock_history = MagicMock()
        mock_history.empty = True
        mock_ticker.return_value.history.return_value = mock_history

        result = get_stock_prices(["AAPL"])

        assert result == [{"stock": "AAPL", "price": 0.0}]


class TestGetCardsInfo:

    def test_get_cards_info(self, sample_df: pd.DataFrame) -> None:
        start = datetime(2021, 12, 1)
        end = datetime(2021, 12, 31)
        result = get_cards_info(sample_df, start, end)
        assert len(result) == 2

    def test_get_cards_info_empty(self) -> None:
        result = get_cards_info(
            pd.DataFrame(), datetime(2021, 1, 1), datetime(2021, 12, 31)
        )
        assert result == []


class TestGetTopTransactions:

    def test_get_top_transactions(self, sample_df: pd.DataFrame) -> None:
        start = datetime(2021, 12, 1)
        end = datetime(2021, 12, 31)
        result = get_top_transactions(sample_df, start, end)
        assert len(result) == 4  # меньше 5 транзакций в фикстуре


class TestMainPage:

    @patch("src.views.get_stock_prices")
    @patch("src.views.get_currency_rates")
    @patch("src.views.pd.read_excel")
    @patch("src.views.read_user_settings")
    def test_main_page(
        self,
        mock_settings: MagicMock,
        mock_read_excel: MagicMock,
        mock_currency: MagicMock,
        mock_stocks: MagicMock,
        sample_df: pd.DataFrame,
    ) -> None:
        mock_settings.return_value = {
            "user_currencies": ["USD"],
            "user_stocks": ["AAPL"],
        }
        mock_read_excel.return_value = sample_df
        mock_currency.return_value = [{"currency": "USD", "rate": 73.21}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.12}]

        result = main_page("2021-12-20 14:30:00")

        assert "greeting" in result
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result
