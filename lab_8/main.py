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
    session: aiohttp.ClientSession,
    url: str,
    output: Path,
    index: int,
    semaphore: asyncio.Semaphore,
) -> None:
    """Download an image within the concurrency limit."""
    try:
        async with semaphore, session.get(url) as response:
            response.raise_for_status()

            if not response.content_type.startswith("image/"):
                raise ValueError("Response is not an image.")

            extension = mimetypes.guess_extension(response.content_type) or ".img"
            file_path = output / f"image_{index}{extension}"
            data = await response.read()

            async with aiofiles.open(file_path, "wb") as file:
                await file.write(data)

            print(f"Downloaded {file_path.name}")
    except TimeoutError:
        print(f"Failed to download {url}: request timed out.")
    except (aiohttp.ClientError, OSError, ValueError) as error:
        print(f"Failed to download {url}: {error}")


async def main() -> None:
    """Read URLs and download images concurrently."""
    args = parse_args()

    try:
        urls = read_urls(args.file)
        args.output.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, csv.Error) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Found {len(urls)} image URLs")

    semaphore = asyncio.Semaphore(args.concurrency)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            download_image(session, url, args.output, index, semaphore)
            for index, url in enumerate(urls, start=1)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
