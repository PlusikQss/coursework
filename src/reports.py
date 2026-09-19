import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("reports")
logger.setLevel(logging.DEBUG)

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "reports.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Папка для сохранения отчётов
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def save_report(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для сохранения результата отчёта в файл.

    Параметры
    ---------
    filename : Optional[str]
        Имя файла для сохранения. Если не указано — используется имя по умолчанию.

    Возвращает
    ----------
    Callable
        Декорированную функцию.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename:
                file_path = REPORTS_DIR / filename
            else:
                file_path = REPORTS_DIR / f"{func.__name__}_report.json"

            # Сохраняем результат
            try:
                if isinstance(result, pd.DataFrame):
                    # Датафрейм → JSON-строку
                    data = result.to_dict(orient="records")
                else:
                    data = result

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

                logger.debug(f"Отчёт сохранён: {file_path}")
            except Exception as exc:
                logger.error(f"Ошибка сохранения отчёта: {exc}")

            return result

        return wrapper

    return decorator


def _parse_date(date: Optional[str]) -> datetime:
    """Парсит дату из строки или возвращает текущую."""
    if date is None:
        return datetime.now()

    # Пробуем разные форматы
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date, fmt)
        except ValueError:
            continue

    return datetime.now()


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Преобразует даты в датафрейме."""
    df = df.copy()

    # Ищем колонку с датой
    date_col = None
    for col in df.columns:
        if "дата операции" in col.lower():
            date_col = col
            break

    if date_col is None:
        return df

    df[date_col] = pd.to_datetime(
        df[date_col], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )
    return df


@save_report()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Возвращает траты по заданной категории за последние три месяца.

    Параметры
    ---------
    transactions : pd.DataFrame
        Датафрейм с транзакциями.
    category : str
        Название категории.
    date : Optional[str]
        Дата отсчёта (по умолчанию — текущая).

    Возвращает
    ----------
    pd.DataFrame
        Траты по категории.
    """
    logger.debug(f"Траты по категории '{category}', дата: {date}")

    current_date = _parse_date(date)
    three_months_ago = current_date - timedelta(days=90)

    df = _prepare_dataframe(transactions)
    date_col = None
    for col in df.columns:
        if "дата операции" in col.lower():
            date_col = col
            break

    if date_col is None:
        return pd.DataFrame()

    # Фильтруем по категории и периоду
    filtered = df[
        (df["Категория"] == category)
        & (df[date_col] >= three_months_ago)
        & (df[date_col] <= current_date)
    ]

    result = filtered[
        ["Дата операции", "Сумма операции", "Категория", "Описание"]
    ].copy()
    logger.debug(f"Найдено записей: {len(result)}")
    return result


@save_report()
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Возвращает средние траты по дням недели за последние три месяца.

    Параметры
    ---------
    transactions : pd.DataFrame
        Датафрейм с транзакциями.
    date : Optional[str]
        Дата отсчёта (по умолчанию — текущая).

    Возвращает
    ----------
    pd.DataFrame
        Средние траты по дням недели.
    """
    logger.debug(f"Траты по дням недели, дата: {date}")

    current_date = _parse_date(date)
    three_months_ago = current_date - timedelta(days=90)

    df = _prepare_dataframe(transactions)
    date_col = None
    for col in df.columns:
        if "дата операции" in col.lower():
            date_col = col
            break

    if date_col is None:
        return pd.DataFrame()

    # Фильтруем по периоду
    filtered = df[
        (df[date_col] >= three_months_ago)
        & (df[date_col] <= current_date)
        & (df["Сумма операции"] < 0)
    ].copy()

    # Добавляем день недели
    filtered["weekday"] = filtered[date_col].dt.day_name()
    filtered["abs_amount"] = filtered["Сумма операции"].abs()

    # Средние траты по дням
    result = (
        filtered.groupby("weekday")["abs_amount"]
        .mean()
        .reset_index()
        .rename(columns={"weekday": "День недели", "abs_amount": "Средние траты"})
    )

    logger.debug(f"Результат: {len(result)} дней")
    return result
