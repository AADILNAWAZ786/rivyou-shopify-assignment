import csv
import json
import time

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from .config import MAX_WORKERS
from .config import OUTPUT_DIR

from .crawler import SiteCrawler
from .crawler import choose_base_url

from .detection import analyze

from .extractors import extract_category
from .extractors import extract_contacts
from .extractors import extract_description
from .extractors import extract_logo
from .extractors import extract_socials
from .extractors import extract_state_from_address_data

from .utils import canonical_host


FINAL_FIELDS = [
    "domain_url",
    "contacts",
    "socials",
    "category",
    "tagline_description",
    "logo",
    "state",
]


def process_candidate(candidate):

    start_time = time.time()

    try:

        base_url = choose_base_url(
            candidate
        )

        host = canonical_host(
            base_url
        )

        crawler = SiteCrawler(
            base_url
        )

        # ---------------------------------
        # Step 1: Homepage
        # ---------------------------------

        homepage = crawler.get_homepage()

        if not homepage:

            return None, time.time() - start_time

        # ---------------------------------
        # Step 2: Check Shopify first
        # ---------------------------------

        first_check = analyze(
            homepage.html,
            host,
            homepage.text
        )

        if not first_check["shopify"]:

            return None, time.time() - start_time

        # ---------------------------------
        # Step 3: Check India from homepage
        # ---------------------------------

        pages = [homepage]

        detection = first_check

        # ---------------------------------
        # Step 4:
        # If India is not confirmed or
        # state is missing, get one extra page.
        # ---------------------------------

        if (
            not detection["india"]
            or not detection["state"]
        ):

            extra_pages = crawler.get_extra_pages(
                homepage,
                max_pages=1
            )

            pages.extend(
                extra_pages
            )

            all_text = ""

            for page in pages:

                all_text = (
                    all_text
                    + " "
                    + page.text
                )

            detection = analyze(
                homepage.html,
                host,
                all_text
            )

        # ---------------------------------
        # Step 5: Final India check
        # ---------------------------------

        if not detection["india"]:

            return None, time.time() - start_time

        # ---------------------------------
        # Step 6: Extract contacts
        # ---------------------------------

        emails, phones = extract_contacts(
            pages
        )

        # ---------------------------------
        # Step 7: Extract socials
        # ---------------------------------

        socials = extract_socials(
            pages
        )

        # ---------------------------------
        # Step 8: Extract state
        # ---------------------------------

        state = extract_state_from_address_data(
            pages
        )

        if not state:

            state = detection["state"]

        # ---------------------------------
        # Step 9: Extract category
        # ---------------------------------

        category = extract_category(
            pages
        )

        # ---------------------------------
        # Step 10: Extract description
        # ---------------------------------

        description = extract_description(
            pages
        )

        # ---------------------------------
        # Step 11: Extract logo
        # ---------------------------------

        logo = extract_logo(
            pages
        )

        # ---------------------------------
        # Step 12: Final record
        # ---------------------------------

        record = {

            "domain_url":
                homepage.url,

            "contacts":
                json.dumps(
                    {
                        "emails": emails,
                        "phones": phones
                    }
                ),

            "socials":
                json.dumps(
                    socials
                ),

            "category":
                category,

            "tagline_description":
                description,

            "logo":
                logo,

            "state":
                state or "",

            "audit": {

                "source_candidate":
                    candidate,

                "final_url":
                    homepage.url,

                "shopify_score":
                    detection[
                        "shopify_score"
                    ],

                "shopify_signals":
                    detection[
                        "shopify_signals"
                    ],

                "india_score":
                    detection[
                        "india_score"
                    ],

                "india_evidence":
                    detection[
                        "india_evidence"
                    ],

                "robots_status":
                    crawler.robots_status
            }
        }

        return (
            record,
            time.time() - start_time
        )

    except Exception as error:

        print(
            "\n[ERROR]",
            candidate,
            error
        )

        return (
            None,
            time.time() - start_time
        )


def deduplicate(records):

    result = []

    seen = set()

    for record in records:

        host = canonical_host(
            record["domain_url"]
        )

        if host in seen:

            continue

        seen.add(host)

        result.append(record)

    return result


def write_outputs(records):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    records = deduplicate(
        records
    )

    csv_file = (
        OUTPUT_DIR
        / "indian_shopify_stores.csv"
    )

    audit_file = (
        OUTPUT_DIR
        / "audit.jsonl"
    )

    summary_file = (
        OUTPUT_DIR
        / "run_summary.json"
    )

    # ---------------------------------
    # Write CSV
    # ---------------------------------

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FINAL_FIELDS
        )

        writer.writeheader()

        for record in records:

            row = {}

            for field in FINAL_FIELDS:

                row[field] = record[field]

            writer.writerow(row)

    # ---------------------------------
    # Write audit file
    # ---------------------------------

    with open(
        audit_file,
        "w",
        encoding="utf-8"
    ) as file:

        for record in records:

            file.write(
                json.dumps(
                    record["audit"]
                )
                + "\n"
            )

    # ---------------------------------
    # Calculate summary
    # ---------------------------------

    email_count = 0
    phone_count = 0
    social_count = 0
    logo_count = 0
    state_count = 0
    unknown_category_count = 0

    for record in records:

        contacts = json.loads(
            record["contacts"]
        )

        socials = json.loads(
            record["socials"]
        )

        if contacts["emails"]:

            email_count += 1

        if contacts["phones"]:

            phone_count += 1

        if socials:

            social_count += 1

        if record["logo"]:

            logo_count += 1

        if record["state"]:

            state_count += 1

        if (
            record["category"]
            == "unknown"
        ):

            unknown_category_count += 1

    summary = {

        "verified_records":
            len(records),

        "email_present":
            email_count,

        "phone_present":
            phone_count,

        "socials_present":
            social_count,

        "logo_present":
            logo_count,

        "state_present":
            state_count,

        "category_unknown":
            unknown_category_count
    }

    # ---------------------------------
    # Write summary
    # ---------------------------------

    with open(
        summary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            indent=2
        )

    return (
        csv_file,
        audit_file,
        summary_file,
        summary
    )


def run(candidates):

    total = len(candidates)

    results = {}

    completed = 0

    total_start_time = time.time()

    print(
        "Total candidates:",
        total
    )

    # ---------------------------------
    # Process 10 websites at the same time
    # ---------------------------------

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_to_candidate = {}

        for candidate in candidates:

            future = executor.submit(
                process_candidate,
                candidate
            )

            future_to_candidate[
                future
            ] = candidate

        for future in as_completed(
            future_to_candidate
        ):

            candidate = (
                future_to_candidate[
                    future
                ]
            )

            try:

                record, site_time = (
                    future.result()
                )

                results[candidate] = {
                    "record": record,
                    "time": site_time
                }

                completed += 1

                print(
                    f"[{completed}/{total}] "
                    f"checked: {candidate} "
                    f"({site_time:.2f} sec)"
                )

            except Exception as error:

                results[candidate] = {
                    "record": None,
                    "time": 0
                }

                completed += 1

                print(
                    f"[{completed}/{total}] "
                    f"error: {candidate} "
                    f"({error})"
                )

    # ---------------------------------
    # Show final results in original order
    # ---------------------------------

    records = []

    for number, candidate in enumerate(
        candidates,
        start=1
    ):

        result = results.get(
            candidate
        )

        if result and result["record"]:

            record = result["record"]

            site_time = result["time"]

            records.append(
                record
            )

            print(
                f"[{number}/{total}] "
                f"VERIFIED: "
                f"{record['domain_url']} "
                f"({site_time:.2f} sec)"
            )

        else:

            site_time = 0

            if result:

                site_time = result["time"]

            print(
                f"[{number}/{total}] "
                f"rejected: "
                f"{candidate} "
                f"({site_time:.2f} sec)"
            )

    # ---------------------------------
    # Total runtime
    # ---------------------------------

    total_time = (
        time.time()
        - total_start_time
    )

    print()
    print(
        f"Total processing time: "
        f"{total_time:.2f} seconds"
    )

    print(
        f"Total processing time: "
        f"{total_time / 60:.2f} minutes"
    )

    return write_outputs(
        records
    )