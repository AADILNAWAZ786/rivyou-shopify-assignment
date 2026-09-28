import argparse
import json

from app.discovery import discover_candidates

from app.pipeline import run


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help=(
            "Number of candidates to process. "
            "0 means all candidates."
        )
    )

    parser.add_argument(
        "--no-common-crawl",
        action="store_true",
        help="Do not use Common Crawl."
    )

    args = parser.parse_args()

    print(
        "Starting Rivyou Shopify "
        "Store Pipeline..."
    )

    # -----------------------------
    # Find candidate websites
    # -----------------------------

    candidates = discover_candidates(
        include_common_crawl=(
            not args.no_common_crawl
        )
    )

    # -----------------------------
    # Apply candidate limit
    # -----------------------------

    if args.limit > 0:

        candidates = candidates[:args.limit]

        print(
            "[RUN] Candidate limit:",
            len(candidates)
        )

    # -----------------------------
    # Check candidates
    # -----------------------------

    if not candidates:

        print(
            "No candidates found."
        )

        return

    (
        csv_file,
        audit_file,
        summary_file,
        summary
    ) = run(candidates)

    # -----------------------------
    # Final result
    # -----------------------------

    print()
    print(
        "=== FINAL RESULTS ==="
    )

    print(
        json.dumps(
            summary,
            indent=2
        )
    )

    print(
        "CSV:",
        csv_file
    )

    print(
        "Audit:",
        audit_file
    )

    print(
        "Summary:",
        summary_file
    )


if __name__ == "__main__":

    main()