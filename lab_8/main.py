import argparse
import asyncio
import csv
import mimetypes
from pathlib import Path

import aiofiles
import aiohttp


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


async def download_image(
    session: aiohttp.ClientSession, url: str, output: Path, index: int
) -> None:
    """Download an image and save it to the output directory."""
    async with session.get(url) as response:
        response.raise_for_status()

        if not response.content_type.startswith("image/"):
            raise ValueError("Response is not an image.")

        extension = mimetypes.guess_extension(response.content_type) or ".img"
        file_path = output / f"image_{index}{extension}"

        async with aiofiles.open(file_path, "wb") as file:
            await file.write(await response.read())

        print(f"Downloaded {file_path.name}")


async def main() -> None:
    """Read URLs and download images."""
    args = parse_args()
    urls = read_urls(args.file)

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(urls)} image URLs")

    async with aiohttp.ClientSession() as session:
        for index, url in enumerate(urls, start=1):
            await download_image(session, url, args.output, index)


if __name__ == "__main__":
    asyncio.run(main())
