import json
import logging
from pathlib import Path

from src.reports import spending_by_category, spending_by_weekday
from src.services import investment_bank, search_phone_numbers, simple_search
from src.utils import read_excel_file
from src.views import main_page

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / "main.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def _print_menu() -> None:
    """Печатает главное меню."""
    print("\n" + "=" * 50)
    print("Выберите действие:")
    print("1. Главная страница (JSON)")
    print("2. Инвесткопилка")
    print("3. Простой поиск")
    print("4. Поиск по телефонам")
    print("5. Траты по категории")
    print("6. Траты по дням недели")
    print("0. Выход")
    print("=" * 50)


def _handle_main_page(df) -> None:
    """Обрабатывает пункт 'Главная страница'."""
    date_input = input("Введите дату и время (YYYY-MM-DD HH:MM:SS): ").strip()
    try:
        result = main_page(date_input)
        print(result)
    except Exception as exc:
        print(f"Ошибка: {exc}")


def _handle_investment_bank(df) -> None:
    """Обрабатывает пункт 'Инвесткопилка'."""
    month = input("Введите месяц (YYYY-MM): ").strip()
    limit_str = input("Введите лимит округления (10/50/100): ").strip()

    try:
        limit = int(limit_str)
    except ValueError:
        print("Некорректный лимит. Использую 50.")
        limit = 50

    transactions = df.to_dict(orient="records")
    result = investment_bank(month, transactions, limit)
    print(f"Сумма, которую удалось бы отложить: {result:.2f} ₽")


def _handle_simple_search(df) -> None:
    """Обрабатывает пункт 'Простой поиск'."""
    query = input("Введите строку для поиска: ").strip()
    transactions = df.to_dict(orient="records")
    result = simple_search(transactions, query)

    print(f"\nНайдено транзакций: {len(result)}")
    for tx in result[:10]:
        print(
            f"  {tx.get('Дата операции')} | {tx.get('Категория')} | {tx.get('Описание')}"
        )

    if len(result) > 10:
        print(f"  ... и ещё {len(result) - 10}")


def _handle_phone_search(df) -> None:
    """Обрабатывает пункт 'Поиск по телефонам'."""
    transactions = df.to_dict(orient="records")
    result = search_phone_numbers(transactions)

    print(f"\nНайдено транзакций с телефонами: {len(result)}")
    for tx in result[:10]:
        print(f"  {tx.get('Дата операции')} | {tx.get('Описание')}")


def _handle_spending_by_category(df) -> None:
    """Обрабатывает пункт 'Траты по категории'."""
    category = input("Введите категорию: ").strip()
    date_input = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ").strip()
    date = date_input if date_input else None

    result = spending_by_category(df, category, date)
    print(f"\nНайдено записей: {len(result)}")
    if not result.empty:
        print(result.head(10).to_string())


def _handle_spending_by_weekday(df) -> None:
    """Обрабатывает пункт 'Траты по дням недели'."""
    date_input = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ").strip()
    date = date_input if date_input else None

    result = spending_by_weekday(df, date)
    print("\nСредние траты по дням недели:")
    print(result.to_string())


def main() -> None:
    """Основная логика программы."""
    logger.debug("Запуск main")

    print("Загрузка данных...")
    df = read_excel_file("data/operations.xlsx")

    if df.empty:
        print("Не удалось загрузить данные.")
        return

    print(f"Загружено транзакций: {len(df)}")

    while True:
        _print_menu()
        choice = input("Ваш выбор: ").strip()

        try:
            if choice == "1":
                _handle_main_page(df)
            elif choice == "2":
                _handle_investment_bank(df)
            elif choice == "3":
                _handle_simple_search(df)
            elif choice == "4":
                _handle_phone_search(df)
            elif choice == "5":
                _handle_spending_by_category(df)
            elif choice == "6":
                _handle_spending_by_weekday(df)
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("Некорректный выбор. Попробуйте снова.")
        except Exception as exc:
            logger.error(f"Ошибка в main: {exc}")
            print(f"Произошла ошибка: {exc}")


if __name__ == "__main__":
    main()
