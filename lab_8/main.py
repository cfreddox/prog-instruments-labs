import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Asynchronous image downloader")
    parser.add_argument("-f", "--file", type=Path, default=Path("images.csv"))
    parser.add_argument("-o", "--output", type=Path, default=Path("downloads"))
    parser.add_argument("-c", "--concurrency", type=int, default=20)

    args = parser.parse_args()

    if args.concurrency <= 0:
        parser.error("Concurrency must be positive.")

    return args


def read_urls(file_path: Path) -> list[str]:
    """Read image URLs from a CSV file."""
    with file_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or "url" not in reader.fieldnames:
            raise ValueError("CSV file must contain a 'url' column.")

        return [row["url"].strip() for row in reader if row["url"]]


def main() -> None:
    """Read input data and display image URLs."""
    args = parse_args()
    urls = read_urls(args.file)

    print(f"Found {len(urls)} image URLs")

    for url in urls:
        print(url)


if __name__ == "__main__":
    main()
