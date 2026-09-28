import json

import requests

from .config import (
    COMMON_CRAWL_ENABLED,
    COMMON_CRAWL_LIMIT_PER_QUERY,
    COMMON_CRAWL_PATTERNS,
    PUBLIC_SEED_URL,
    SEED_FILE,
    USER_AGENT,
    REQUEST_TIMEOUT,
)
from .utils import normalize_url

def load_local_seeds():

    urls = []

    if not SEED_FILE.exists():

        return urls

    lines = SEED_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    for line in lines:

        line = line.strip()

        if not line:

            continue

        if line.startswith("#"):

            continue

        url = normalize_url(line)

        if url:

            urls.append(url)

    return urls


def load_public_seed():

    urls = []

    response = requests.get(
        PUBLIC_SEED_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    response.raise_for_status()

    lines = response.text.splitlines()

    for line in lines:

        line = line.strip()

        line = line.strip('"')

        if (
            not line.startswith("http://")
            and not line.startswith("https://")
        ):

            continue

        url = normalize_url(line)

        if url:

            urls.append(url)

    return urls


def latest_common_crawl_collection():

    url = "https://index.commoncrawl.org/collinfo.json"

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    response.raise_for_status()

    collections = response.json()

    if len(collections) == 0:

        return None

    return collections[0]["id"]


def common_crawl_candidates():

    if not COMMON_CRAWL_ENABLED:

        return []

    urls = []

    try:

        collection = (
            latest_common_crawl_collection()
        )

    except Exception as error:

        print(
            "[WARN] Common Crawl error:",
            error
        )

        return urls

    if not collection:

        return urls

    index_url = (
        "https://index.commoncrawl.org/"
        + collection
        + "-index"
    )

    for pattern in COMMON_CRAWL_PATTERNS:

        try:

            params = {

                "url": pattern,

                "output": "json",

                "filter": [
                    "status:200",
                    "mime:text/html"
                ],

                "collapse": "urlkey",

                "limit": COMMON_CRAWL_LIMIT_PER_QUERY
            }

            response = requests.get(
                index_url,
                params=params,
                timeout=60,
                headers={
                    "User-Agent": USER_AGENT
                }
            )

            if response.status_code != 200:

                print(
                    "[WARN] Common Crawl returned",
                    response.status_code
                )

                continue

            lines = response.text.splitlines()

            for line in lines:

                try:

                    record = json.loads(line)

                    url = normalize_url(
                        record.get(
                            "url",
                            ""
                        )
                    )

                    if url:

                        urls.append(url)

                except json.JSONDecodeError:

                    continue

        except Exception as error:

            print(
                "[WARN] Common Crawl pattern error:",
                error
            )

    return urls


def remove_duplicate_urls(urls):

    result = []

    seen = set()

    for url in urls:

        url = normalize_url(url)

        if not url:

            continue

        if url in seen:

            continue

        seen.add(url)

        result.append(url)

    return result


def discover_candidates(
    include_common_crawl=True
):

    all_urls = []

    try:

        urls = load_public_seed()

        print(
            "[DISCOVERY] Public seed:",
            len(urls)
        )

        all_urls.extend(urls)

    except Exception as error:

        print(
            "[WARN] Public seed failed:",
            error
        )

    urls = load_local_seeds()

    print(
        "[DISCOVERY] Local seeds:",
        len(urls)
    )

    all_urls.extend(urls)

    if include_common_crawl:

        urls = common_crawl_candidates()

        print(
            "[DISCOVERY] Common Crawl:",
            len(urls)
        )

        all_urls.extend(urls)

    all_urls = remove_duplicate_urls(
        all_urls
    )

    print(
        "[DISCOVERY] Total unique candidates:",
        len(all_urls)
    )

    return all_urls
