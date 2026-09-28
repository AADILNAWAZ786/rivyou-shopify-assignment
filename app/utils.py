import re
from urllib.parse import urljoin, urlparse, urlunparse

import tldextract


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_url(url):
    if not url:
        return None

    url = url.strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc:
        return None

    hostname = parsed.hostname

    if not hostname:
        return None

    path = parsed.path

    if not path:
        path = "/"

    if path != "/":
        path = path.rstrip("/")

    new_url = urlunparse(
        (
            parsed.scheme.lower(),
            hostname.lower(),
            path,
            "",
            "",
            "",
        )
    )

    return new_url


def canonical_host(url):
    parsed = urlparse(url)

    host = parsed.hostname or ""

    host = host.lower()

    if host.startswith("www."):
        host = host[4:]

    return host


def absolute_url(base_url, href):
    if not href:
        return None

    href = href.strip()

    if href.startswith("mailto:"):
        return None

    if href.startswith("tel:"):
        return None

    if href.startswith("javascript:"):
        return None

    if href.startswith("#"):
        return None

    full_url = urljoin(base_url, href)

    return normalize_url(full_url)


def remove_duplicates(items):
    result = []

    seen = set()

    for item in items:
        if not item:
            continue

        if isinstance(item, str):
            item = item.strip()

        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
