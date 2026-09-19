from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.reports import spending_by_category, spending_by_weekday


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Тестовый датафрейм с транзакциями."""
    today = datetime.now()
    return pd.DataFrame(
        {
            "Дата операции": [
                (today - timedelta(days=10)).strftime("%d.%m.%Y %H:%M:%S"),
                (today - timedelta(days=20)).strftime("%d.%m.%Y %H:%M:%S"),
                (today - timedelta(days=30)).strftime("%d.%m.%Y %H:%M:%S"),
                (today - timedelta(days=60)).strftime("%d.%m.%Y %H:%M:%S"),
                (today - timedelta(days=100)).strftime("%d.%m.%Y %H:%M:%S"),
            ],
            "Сумма операции": [-1000.0, -500.0, -2000.0, -300.0, -1500.0],
            "Категория": [
                "Супермаркеты",
                "Супермаркеты",
                "ЖКХ",
                "Супермаркеты",
                "Супермаркеты",
            ],
            "Описание": ["Лента", "Пятёрочка", "ЖКУ", "Магнит", "Ашан"],
        }
    )


class TestSpendingByCategory:

    def test_spending_by_category(self, sample_df: pd.DataFrame) -> None:
        result = spending_by_category(sample_df, "Супермаркеты")
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_spending_by_category_with_date(self, sample_df: pd.DataFrame) -> None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        result = spending_by_category(sample_df, "Супермаркеты", date_str)
        assert isinstance(result, pd.DataFrame)

    def test_spending_by_category_empty(self, sample_df: pd.DataFrame) -> None:
        result = spending_by_category(sample_df, "Несуществующая")
        assert result.empty

    def test_spending_by_category_invalid_date(self, sample_df: pd.DataFrame) -> None:
        result = spending_by_category(sample_df, "Супермаркеты", "неправильная дата")
        assert isinstance(result, pd.DataFrame)


class TestSpendingByWeekday:

    def test_spending_by_weekday(self, sample_df: pd.DataFrame) -> None:
        result = spending_by_weekday(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_spending_by_weekday_with_date(self, sample_df: pd.DataFrame) -> None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        result = spending_by_weekday(sample_df, date_str)
        assert isinstance(result, pd.DataFrame)

    def test_spending_by_weekday_columns(self, sample_df: pd.DataFrame) -> None:
        result = spending_by_weekday(sample_df)
        if not result.empty:
            assert "День недели" in result.columns
            assert "Средние траты" in result.columns
