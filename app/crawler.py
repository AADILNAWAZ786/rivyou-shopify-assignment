import time

import requests

from bs4 import BeautifulSoup

from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
from urllib.parse import urlparse

from .config import REQUEST_TIMEOUT
from .config import USER_AGENT
from .config import MAX_SITE_TIME
from .config import MAX_HTML_SIZE

from .utils import clean_text
from .utils import absolute_url


class Page:

    def __init__(
        self,
        url,
        status_code,
        html,
        text
    ):

        self.url = url
        self.status_code = status_code
        self.html = html
        self.text = text


class SiteCrawler:

    def __init__(self, base_url):

        self.base_url = base_url

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": USER_AGENT
            }
        )

        self.robots = None

        self.robots_status = "unknown"

        self.start_time = time.time()

    def time_left(self):

        elapsed = (
            time.time()
            - self.start_time
        )

        return (
            MAX_SITE_TIME
            - elapsed
        )

    def can_continue(self):

        return self.time_left() > 0

    def load_robots(self):

        if not self.can_continue():

            return

        robots_url = (
            self.base_url.rstrip("/")
            + "/robots.txt"
        )

        try:

            remaining = self.time_left()

            if remaining <= 0:

                return

            connect_timeout = min(
                REQUEST_TIMEOUT[0],
                remaining
            )

            read_timeout = min(
                REQUEST_TIMEOUT[1],
                remaining
            )

            response = self.session.get(
                robots_url,
                timeout=(
                    connect_timeout,
                    read_timeout
                ),
                allow_redirects=False
            )

            self.robots = RobotFileParser()

            self.robots.set_url(
                robots_url
            )

            if response.status_code == 404:

                self.robots.parse([])

                self.robots_status = "not_found"

            elif response.status_code == 200:

                self.robots.parse(
                    response.text.splitlines()
                )

                self.robots_status = "loaded"

            elif response.status_code in [
                401,
                403
            ]:

                self.robots = None

                self.robots_status = "blocked"

            else:

                self.robots.parse([])

                self.robots_status = "unknown"

        except requests.RequestException:

            self.robots = None

            self.robots_status = "error"

    def allowed(self, url):

        if self.robots_status == "blocked":

            return False

        if self.robots is None:

            return False

        try:

            return self.robots.can_fetch(
                USER_AGENT,
                url
            )

        except Exception:

            return False

    def get_page(
        self,
        url,
        allow_redirect=True
    ):

        if not self.can_continue():

            return None

        if not self.allowed(url):

            return None

        try:

            remaining = self.time_left()

            if remaining <= 0:

                return None

            connect_timeout = min(
                REQUEST_TIMEOUT[0],
                remaining
            )

            read_timeout = min(
                REQUEST_TIMEOUT[1],
                remaining
            )

            response = self.session.get(
                url,
                timeout=(
                    connect_timeout,
                    read_timeout
                ),
                allow_redirects=False,
                stream=True
            )

            # ---------------------------------
            # Handle one redirect
            # ---------------------------------

            if response.status_code in [
                301,
                302,
                303,
                307,
                308
            ]:

                if not allow_redirect:

                    response.close()

                    return None

                location = response.headers.get(
                    "Location"
                )

                response.close()

                if not location:

                    return None

                new_url = urljoin(
                    url,
                    location
                )

                return self.get_page(
                    new_url,
                    allow_redirect=False
                )

            if response.status_code >= 400:

                response.close()

                return None

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            if (
                "text/html" not in content_type
                and
                "application/xhtml+xml"
                not in content_type
            ):

                response.close()

                return None

            # ---------------------------------
            # Read only limited HTML
            # ---------------------------------

            html_parts = []

            total_size = 0

            for chunk in response.iter_content(
                chunk_size=32 * 1024
            ):

                if not self.can_continue():

                    break

                if not chunk:

                    continue

                html_parts.append(
                    chunk
                )

                total_size += len(chunk)

                if total_size >= MAX_HTML_SIZE:

                    break

            response.close()

            html_bytes = b"".join(
                html_parts
            )

            html = html_bytes.decode(
                "utf-8",
                errors="ignore"
            )

            if not html:

                return None

            soup = BeautifulSoup(
                html,
                "lxml"
            )

            for tag in soup.find_all(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg"
                ]
            ):

                tag.decompose()

            text = soup.get_text(
                " ",
                strip=True
            )

            text = clean_text(
                text
            )

            return Page(
                response.url,
                response.status_code,
                html,
                text
            )

        except requests.RequestException:

            return None

        except Exception:

            return None

    def get_homepage(self):

        self.load_robots()

        if self.robots_status == "blocked":

            return None

        if not self.can_continue():

            return None

        homepage_url = (
            self.base_url.rstrip("/")
            + "/"
        )

        return self.get_page(
            homepage_url
        )

    def find_useful_links(
        self,
        homepage
    ):

        links = []

        soup = BeautifulSoup(
            homepage.html,
            "lxml"
        )

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link.get(
                "href"
            )

            full_url = absolute_url(
                homepage.url,
                href
            )

            if not full_url:

                continue

            link_text = clean_text(
                link.get_text(
                    " ",
                    strip=True
                )
            ).lower()

            full_url_text = (
                full_url.lower()
            )

            score = 0

            if (
                "contact" in link_text
                or
                "contact" in full_url_text
            ):

                score = 5

            elif (
                "about" in link_text
                or
                "about" in full_url_text
            ):

                score = 4

            elif (
                "privacy" in link_text
                or
                "privacy" in full_url_text
            ):

                score = 2

            if score > 0:

                links.append(
                    (
                        score,
                        full_url
                    )
                )

        links.sort(
            reverse=True
        )

        result = []

        for score, url in links:

            if url not in result:

                result.append(
                    url
                )

        return result

    def get_extra_pages(
        self,
        homepage,
        max_pages=1
    ):

        pages = []

        if not self.can_continue():

            return pages

        links = self.find_useful_links(
            homepage
        )

        links = links[:max_pages]

        for url in links:

            if not self.can_continue():

                break

            if url == homepage.url:

                continue

            page = self.get_page(
                url
            )

            if page:

                pages.append(
                    page
                )

        return pages


def choose_base_url(url):

    parsed = urlparse(url)

    scheme = parsed.scheme

    netloc = parsed.netloc

    return scheme + "://" + netloc