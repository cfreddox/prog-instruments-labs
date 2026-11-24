import argparse
import asyncio
import csv
import logging
import mimetypes
from pathlib import Path

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


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
) -> bool:
    """Download an image and report whether it succeeded."""
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

    except TimeoutError:
        logger.error("Failed to download %s: request timed out.", url)
        return False
    except (aiohttp.ClientError, OSError, ValueError) as error:
        logger.error("Failed to download %s: %s", url, error)
        return False

    logger.info("Downloaded %s", file_path.name)
    return True


async def main() -> None:
    """Read URLs and download images concurrently."""
    args = parse_args()

    try:
        urls = read_urls(args.file)
        args.output.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, csv.Error) as error:
        logger.error("%s", error)
        raise SystemExit(1) from error

    logger.info("Found %d image URLs", len(urls))

    semaphore = asyncio.Semaphore(args.concurrency)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            download_image(session, url, args.output, index, semaphore)
            for index, url in enumerate(urls, start=1)
        ]
        results = await asyncio.gather(*tasks)

    successful = sum(results)
    failed = len(results) - successful
    logger.info("Downloaded: %d, failed: %d", successful, failed)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    asyncio.run(main())
