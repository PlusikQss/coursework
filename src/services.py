import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "services.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def investment_bank(
    month: str, transactions: List[Dict[str, Any]], limit: int
) -> float:
    """
    Считает сумму, которую удалось бы отложить в «Инвесткопилку».

    Параметры
    ---------
    month : str
        Месяц в формате 'YYYY-MM'.
    transactions : List[Dict[str, Any]]
        Список транзакций с полями «Дата операции» и «Сумма операции».
    limit : int
        Шаг округления (10, 50 или 100).

    Возвращает
    ----------
    float
        Сумма отложенных средств.
    """
    logger.debug(f"Инвесткопилка: месяц={month}, лимит={limit}")

    total_savings = 0.0

    for transaction in transactions:
        date = str(transaction.get("Дата операции", ""))
        amount = transaction.get("Сумма операции", 0)

        # Конвертируем DD.MM.YYYY HH:MM:SS → YYYY-MM
        try:
            date_dt = pd.to_datetime(date, format="%d.%m.%Y %H:%M:%S")
            date_month = date_dt.strftime("%Y-%m")
        except (ValueError, TypeError):
            continue

        # Проверяем, что транзакция за нужный месяц
        if date_month != month:
            continue

        # Округляем до лимита (только расходы)
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            continue

        if amount_float >= 0:
            continue

        abs_amount = abs(amount_float)
        rounded = ((abs_amount + limit - 1) // limit) * limit
        savings = rounded - abs_amount
        total_savings += savings

    logger.debug(f"Итого отложено: {total_savings}")
    return round(total_savings, 2)


def simple_search(
    transactions: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """
    Простой поиск по описанию или категории.
    """
    logger.debug(f"Простой поиск: {query}")
    if not query:
        return transactions

    query_lower = query.lower()
    result = [
        t
        for t in transactions
        if query_lower in str(t.get("Описание", "")).lower()
        or query_lower in str(t.get("Категория", "")).lower()
    ]
    logger.debug(f"Найдено: {len(result)}")
    return result


def search_phone_numbers(
    transactions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Поиск транзакций, содержащих мобильные номера в описании.
    """
    logger.debug("Поиск по телефонным номерам")

    # Паттерн для российских номеров:
    # +7 921 11-22-33, 8 995 555-55-55, +7 (900) 000-00-00, 89000000000
    phone_pattern = re.compile(
        r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2}"
    )

    result = [
        t for t in transactions if phone_pattern.search(str(t.get("Описание", "")))
    ]
    logger.debug(f"Найдено с телефонами: {len(result)}")
    return result
