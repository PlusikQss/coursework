import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Логер
logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "utils.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def read_excel_file(file_path: str) -> pd.DataFrame:
    """
    Читает Excel-файл с транзакциями.
    """
    logger.debug(f"Чтение Excel-файла: {file_path}")
    try:
        df = pd.read_excel(file_path)
        logger.debug(f"Файл прочитан. Строк: {len(df)}")
        return df
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден.")
        return pd.DataFrame()
    except Exception as exc:
        logger.error(f"Ошибка при чтении Excel: {exc}")
        return pd.DataFrame()


def read_user_settings(file_path: str = "user_settings.json") -> Dict[str, Any]:
    """
    Читает настройки пользователя из JSON-файла.
    """
    logger.debug(f"Чтение настроек: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            settings = json.load(file)
        logger.debug(f"Настройки загружены: {settings}")
        return settings
    except FileNotFoundError:
        logger.error(f"Файл настроек {file_path} не найден.")
        return {"user_currencies": [], "user_stocks": []}
    except json.JSONDecodeError:
        logger.error(f"Некорректный JSON в {file_path}")
        return {"user_currencies": [], "user_stocks": []}


def get_greeting(current_time: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.
    """
    hour = current_time.hour

    if 6 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 18:
        greeting = "Добрый день"
    elif 18 <= hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    logger.debug(f"Время: {hour}ч. Приветствие: {greeting}")
    return greeting


def filter_by_date_range(
    df: pd.DataFrame, start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """
    Фильтрует транзакции по диапазону дат.
    """
    logger.debug(f"Фильтрация по датам: {start_date} - {end_date}")

    if df.empty:
        return df

    # Ищем колонку с датой
    date_column = None
    for col in df.columns:
        if "дата" in col.lower():
            date_column = col
            break

    if date_column is None:
        logger.error("Колонка с датой не найдена.")
        return df

    df[date_column] = pd.to_datetime(
        df[date_column], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )
    filtered = df[
        (df[date_column] >= start_date) & (df[date_column] <= end_date)
    ].copy()

    logger.debug(f"Отфильтровано строк: {len(filtered)}")
    return filtered
