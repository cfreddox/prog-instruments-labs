import argparse
import csv
import json
import re
from pathlib import Path

from checksum import calculate_checksum

VARIANT = 30

PATTERNS = {
    "telephone": re.compile(
        r"\+7-\(\d{3}\)-\d{3}-\d{2}-\d{2}"
    ),
    "http_status_message": re.compile(
        r"\d{3} [A-Za-z][A-Za-z0-9 .!_-]*"
    ),
    "inn": re.compile(r"\d{12}"),
    "identifier": re.compile(r"\d{2}-\d{2}/\d{2}"),
    "ip_v4": re.compile(
        r"(?:\d{1,3}\.){3}\d{1,3}"
    ),
    "latitude": re.compile(
        r"-?(?:90(?:\.0+)?|[0-8]?\d(?:\.\d+)?)"
    ),
    "blood_type": re.compile(r"(?:A|B|AB|O)[+−]"),
    "isbn": re.compile(
        r"(?:\d{1,5}-\d{1,7}-\d{1,7}-[\dX]|\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-[\dX])"
    ),
    "uuid": re.compile(
        r"[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}"
    ),
    "date": re.compile(r"\d{4}-\d{2}-\d{2}"),
}


def is_valid(field: str, value: str) -> bool:
    """Проверяет соответствие значения поля заданному формату и логике.

    Args:
        field (str): Название проверяемого поля.
        value (str): Строковое значение ячейки для проверки.

    Returns:
        bool: True, если значение валидно, иначе False.
    """
    pattern = PATTERNS.get(field)
    if not pattern or pattern.fullmatch(value) is None:
        return False

    if field == "ip_v4":
        return all(
            0 <= int(part) <= 255
            for part in value.split(".")
        )

    return True


def validate_csv(file_path: Path) -> list[int]:
    """Производит построчную валидацию CSV-файла.

    Args:
        file_path (Path): Путь к проверяемому CSV-файлу.

    Returns:
        list[int]: Отсортированный список целочисленных номеров строк,
        содержащих ошибки валидации.

    Raises:
        ValueError: Если заголовки или порядок столбцов в CSV-файле
            не соответствуют ожидаемым.
    """
    invalid_rows = []

    with file_path.open("r", encoding="utf-16", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")

        expected_fields = list(PATTERNS)
        if reader.fieldnames != expected_fields:
            raise ValueError(
                "Заголовки или порядок столбцов CSV "
                f"не соответствуют ожидаемым: {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader):
            if any(
                not is_valid(field, row[field])
                for field in expected_fields
            ):
                invalid_rows.append(row_number)

    return invalid_rows


def save_result(variant: int, checksum: str) -> None:
    """Сохраняет номер варианта и контрольную сумму в файл result.json.

    Args:
        variant (int): Номер варианта.
        checksum (str): Вычисленная MD5 контрольная сумма.
    """
    result = {
        "variant": str(variant),
        "checksum": checksum,
    }

    Path("result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Валидация CSV-файла с использованием регулярных выражений"
    )
    parser.add_argument("csv_file", type=Path,
                        help="Путь к исходному CSV-файлу")
    args = parser.parse_args()

    invalid_rows = validate_csv(args.csv_file)
    checksum = calculate_checksum(invalid_rows)
    save_result(VARIANT, checksum)

    print(f"Всего невалидных строк: {len(invalid_rows)}")
    print(f"Контрольная сумма: {checksum}")
    print("Результат успешно сохранён в result.json")


if __name__ == "__main__":
    main()
