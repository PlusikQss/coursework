import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

from src.utils import filter_by_date_range, get_greeting, read_user_settings

load_dotenv()

# Логер
logger = logging.getLogger("views")
logger.setLevel(logging.DEBUG)

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "views.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает курсы валют через API.

    Параметры
    ---------
    currencies : List[str]
        Список кодов валют (например, ["USD", "EUR"]).

    Возвращает
    ----------
    List[Dict[str, Any]]
        Список словарей с ключами currency и rate.
    """
    logger.debug(f"Запрос курсов валют: {currencies}")
    api_key = os.getenv("API_KEY")
    result = []

    if not api_key:
        logger.error("API_KEY не найден в .env")
        return [{"currency": c, "rate": 0.0} for c in currencies]

    for currency in currencies:
        try:
            url = (
                f"https://api.apilayer.com/exchangerates_data/latest"
                f"?base={currency}&symbols=RUB"
            )
            headers = {"apikey": api_key}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            rate = data.get("rates", {}).get("RUB", 0.0)
            result.append({"currency": currency, "rate": float(rate)})
            logger.debug(f"Курс {currency}: {rate}")
        except Exception as exc:
            logger.error(f"Ошибка получения курса {currency}: {exc}")
            result.append({"currency": currency, "rate": 0.0})

    return result


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает цены акций через yfinance.
    """
    import yfinance as yf

    logger.debug(f"Запрос цен акций: {stocks}")
    result = []

    for stock in stocks:
        try:
            ticker = yf.Ticker(stock)
            data = ticker.history(period="1d")
            if not data.empty:
                price = float(data["Close"].iloc[-1])
            else:
                price = 0.0
            result.append({"stock": stock, "price": round(price, 2)})
            logger.debug(f"Цена {stock}: {price}")
        except Exception as exc:
            logger.error(f"Ошибка получения цены {stock}: {exc}")
            result.append({"stock": stock, "price": 0.0})

    return result


def get_cards_info(
    df: pd.DataFrame, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Формирует информацию по картам.

    Параметры
    ---------
    df : pd.DataFrame
        Датафрейм с транзакциями.
    start_date : datetime
        Начало периода.
    end_date : datetime
        Конец периода.

    Возвращает
    ----------
    List[Dict[str, Any]]
        Список словарей с last_digits, total_spent, cashback.
    """
    logger.debug("Формирование информации по картам")
    if df.empty:
        return []

    period_df = filter_by_date_range(df, start_date, end_date)
    if period_df.empty:
        return []

    # Фильтруем только расходы (Сумма платежа < 0)
    expenses = period_df[period_df["Сумма платежа"] < 0].copy()
    expenses["abs_amount"] = expenses["Сумма платежа"].abs()

    cards = []
    for card in expenses["Номер карты"].dropna().unique():
        card_expenses = expenses[expenses["Номер карты"] == card]
        total_spent = float(card_expenses["abs_amount"].sum())
        cashback = round(total_spent / 100, 2)
        last_digits = str(card).replace("*", "")[-4:] if card else ""

        cards.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": cashback,
            }
        )

    logger.debug(f"Найдено карт: {len(cards)}")
    return cards


def get_top_transactions(
    df: pd.DataFrame, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Возвращает топ-5 транзакций по сумме платежа.

    Параметры
    ---------
    df : pd.DataFrame
        Датафрейм с транзакциями.
    start_date : datetime
        Начало периода.
    end_date : datetime
        Конец периода.

    Возвращает
    ----------
    List[Dict[str, Any]]
        Список из 5 транзакций.
    """
    logger.debug("Формирование топ-5 транзакций")
    if df.empty:
        return []

    period_df = filter_by_date_range(df, start_date, end_date)
    if period_df.empty:
        return []

    period_df = period_df.copy()
    period_df["abs_amount"] = period_df["Сумма платежа"].abs()
    top5 = period_df.nlargest(5, "abs_amount")

    result = []
    for _, row in top5.iterrows():
        date_val = row["Дата операции"]
        if pd.notna(date_val):
            date_str = pd.to_datetime(date_val).strftime("%d.%m.%Y")
        else:
            date_str = ""

        result.append(
            {
                "date": date_str,
                "amount": float(row["Сумма платежа"]),
                "category": str(row.get("Категория", "")),
                "description": str(row.get("Описание", "")),
            }
        )

    return result


def main_page(date_string: str) -> str:
    """
    Главная функция для страницы «Главная».

    Параметры
    ---------
    date_string : str
        Дата и время в формате YYYY-MM-DD HH:MM:SS.

    Возвращает
    ----------
    str
        JSON-ответ.
    """
    logger.debug(f"Вызов main_page с датой: {date_string}")

    current_dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    start_date = current_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = current_dt

    df = pd.read_excel("data/operations.xlsx")

    settings = read_user_settings()
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])

    response = {
        "greeting": get_greeting(current_dt),
        "cards": get_cards_info(df, start_date, end_date),
        "top_transactions": get_top_transactions(df, start_date, end_date),
        "currency_rates": get_currency_rates(currencies),
        "stock_prices": get_stock_prices(stocks),
    }

    return json.dumps(response, ensure_ascii=False, indent=2)
