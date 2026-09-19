from typing import Any, Dict, List

import pytest

from src.services import (
    investment_bank,
    search_phone_numbers,
    simple_search,
)


@pytest.fixture
def transactions() -> List[Dict[str, Any]]:
    return [
        {
            "Дата операции": "2021-12-01 10:00:00",
            "Сумма операции": -1712.0,
            "Описание": "Покупка в магазине",
            "Категория": "Супермаркеты",
        },
        {
            "Дата операции": "2021-12-15 12:00:00",
            "Сумма операции": -338.0,
            "Описание": "Я МТС +7 921 11-22-33",
            "Категория": "Связь",
        },
        {
            "Дата операции": "2021-12-20 14:00:00",
            "Сумма операции": -5000.0,
            "Описание": "Перевод Валерий А.",
            "Категория": "Переводы",
        },
        {
            "Дата операции": "2022-01-05 10:00:00",
            "Сумма операции": -100.0,
            "Описание": "Такси",
            "Категория": "Транспорт",
        },
    ]


class TestInvestmentBank:

    @pytest.mark.parametrize(
        "month, limit, expected_min",
        [
            ("2021-12", 50, 0),
            ("2021-12", 10, 0),
            ("2021-12", 100, 0),
        ],
    )
    def test_investment_bank(
        self,
        transactions: List[Dict[str, Any]],
        month: str,
        limit: int,
        expected_min: float,
    ) -> None:
        result = investment_bank(month, transactions, limit)
        assert isinstance(result, float)
        assert result >= expected_min

    def test_investment_bank_empty(self) -> None:
        result = investment_bank("2021-12", [], 50)
        assert result == 0.0

    def test_investment_bank_wrong_month(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        result = investment_bank("2020-01", transactions, 50)
        assert result == 0.0


class TestSimpleSearch:

    def test_search_by_description(self, transactions: List[Dict[str, Any]]) -> None:
        result = simple_search(transactions, "МТС")
        assert len(result) == 1
        assert "МТС" in result[0]["Описание"]

    def test_search_by_category(self, transactions: List[Dict[str, Any]]) -> None:
        result = simple_search(transactions, "Переводы")
        assert len(result) == 1

    def test_search_case_insensitive(self, transactions: List[Dict[str, Any]]) -> None:
        result1 = simple_search(transactions, "мтс")
        result2 = simple_search(transactions, "МТС")
        assert len(result1) == len(result2) == 1

    def test_search_empty_query(self, transactions: List[Dict[str, Any]]) -> None:
        result = simple_search(transactions, "")
        assert len(result) == len(transactions)


class TestSearchPhoneNumbers:

    def test_search_phones(self, transactions: List[Dict[str, Any]]) -> None:
        result = search_phone_numbers(transactions)
        assert len(result) == 1

    @pytest.mark.parametrize(
        "description, found",
        [
            ("Я МТС +7 921 11-22-33", True),
            ("Тинькофф Мобайл +7 995 555-55-55", True),
            ("МТС Mobile +7 981 333-44-55", True),
            ("+7 (900) 000-00-00", True),
            ("89000000000", True),
            ("Обычная покупка", False),
            ("Перевод Валерий А.", False),
        ],
    )
    def test_phone_patterns(self, description: str, found: bool) -> None:
        txns = [{"Описание": description}]
        result = search_phone_numbers(txns)
        assert (len(result) == 1) == found
