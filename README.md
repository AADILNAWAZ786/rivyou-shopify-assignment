# SDE Intern Assignment - Discover Indian Shopify Stores

## Objective

Build a reproducible pipeline to discover Shopify storefronts, verify that the storefront is Shopify-powered and India-based, and extract the requested structured fields:

1. Domain URL
2. All discoverable email addresses and phone numbers
3. Social links
4. Category
5. Tagline/description using the store's own wording where possible
6. Brand logo URL, not favicon
7. Indian state

The pipeline separates **candidate discovery** from **verification**. A public list or Common Crawl result is treated only as a lead. A row is written to the final dataset only after live verification.

## Project structure

```text
rivyou-shopify-assignment/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── crawler.py
│   ├── detection.py
│   ├── discovery.py
│   ├── extractors.py
│   ├── pipeline.py
│   └── utils.py
│
├── data/
│   ├── raw/
│   ├── outputs/
│   └── seeds.txt
│
├── tests/
│   └── test_extractors.py
│
├── requirements.txt
├── run.py
├── .gitignore
└── README.md
```

## 1. Candidate discovery

The pipeline uses two free/open discovery paths:

### Public seed list

A publicly available GitHub seed list is downloaded at runtime:

`https://github.com/TeamDukaan/performance/blob/master/shopify%20stores%20-%20shopify.csv`

The file is treated only as a candidate source. Each URL is normalized and verified again against the live website.

### Common Crawl

The pipeline also uses the Common Crawl CDXJ index to add more candidates. The latest available collection is discovered through `collinfo.json`. The query is intentionally limited and uses a small result cap so the index is not overloaded.

Patterns used by default:

```text
*.myshopify.com/*
*.in/cdn/shop/*
*.co.in/cdn/shop/*
```

Common Crawl data is public and free to access. See: https://commoncrawl.org/get-started

## 2. URL normalization and deduplication

Candidate URLs are normalized by:

- adding HTTPS when no scheme is supplied
- removing URL fragments and query strings
- normalizing hostnames
- removing a leading `www.` when comparing hosts
- deduplicating by normalized host

The final output prefers the actual URL returned after live redirects. This means a `myshopify.com` candidate that redirects to a custom domain can end up represented by the custom domain.

## 3. Shopify verification

A site is not considered Shopify solely because of its domain suffix.

The detector searches the homepage HTML for several Shopify storefront signals, including:

- `cdn.shopify.com`
- `window.Shopify`
- `Shopify.theme`
- `Shopify.routes`
- `shopify-section`
- `shopify-payment-button`
- `/cdn/shop/`
- `myshopify.com`

Signals have different weights. A candidate must reach the configured Shopify confidence threshold before it can become a verified record.

The detector records the matched signals in `audit.jsonl` so the decision is inspectable.

Shopify documentation confirms that storefront assets can be served through Shopify's CDN and that the `window.Shopify` object is available in storefront themes. See:

- https://shopify.dev/docs/storefronts/themes/best-practices/performance/use-shopify-cdn
- https://shopify.dev/docs/storefronts/themes/best-practices/performance/load-critical-resources-before-content-for-header

## 4. India verification

The definition used in this project is:

> A storefront is treated as India-based only when the website exposes credible India-specific business evidence. A `.in` domain or INR currency by itself is not sufficient.

India evidence is collected from visible site text and address information. Signals include:

- explicit mention of India/Bharat
- Indian state names
- GSTIN pattern
- Indian phone numbers with `+91` or an Indian local dialing prefix
- `.in` / `.co.in` domain as supporting evidence
- Indian postal-code-like values as supporting evidence

The verifier requires a strong India signal. Domain suffix alone never verifies India.

## 5. robots.txt and crawling policy

Before fetching a store, the crawler retrieves `/robots.txt` and checks the configured crawler user-agent against its rules.

The crawler:

- uses a descriptive user-agent
- waits between page requests on the same site
- uses bounded response sizes
- uses connection timeouts
- does not crawl the entire site
- requests only a small set of likely contact/about/policy pages
- skips a site if `robots.txt` explicitly blocks the crawler or cannot be evaluated safely

Shopify documents that `robots.txt` is available at `/robots.txt` and can contain user-agent-specific rules. See:

https://shopify.dev/docs/storefronts/themes/seo/robots-txt

## 6. Pages crawled


For each candidate, the crawler first requests the homepage.

If the homepage does not provide enough India evidence or a state,
the crawler selects at most one useful internal page, prioritizing
contact, about, privacy, and similar pages.

This keeps the crawl bounded and avoids unrestricted site crawling.
Missing or blocked pages are ignored.

## 7. Contact extraction

Emails are collected from:

- page HTML
- visible page text
- `mailto:` links

Phone numbers are collected from:

- page text
- `tel:` links

The final CSV stores contacts as a JSON object inside the cell:

```json
{"emails": ["hello@example.in"], "phones": ["+91 9876543210"]}
```

## 8. Social extraction

Social links are discovered from `<a href>` elements and normalized by hostname.

Supported networks:

- Instagram
- Facebook
- Twitter/X
- LinkedIn
- YouTube

The final CSV stores a JSON object, for example:

```json
{
  "instagram": ["https://instagram.com/example"],
  "facebook": ["https://facebook.com/example"]
}
```

## 9. Category extraction

Category is inferred from store-owned text such as:

- page titles
- descriptions
- product/category wording
- visible homepage/contact/about content

A lightweight keyword classifier is used so the classification is deterministic and reproducible.

Possible categories include skincare, cosmetics, apparel, jewellery, home decor, food & beverages, electronics, health & wellness, pets, stationery, and footwear.

If no category signal is found, the output is `unknown` instead of inventing a category.

## 10. Tagline / description extraction

Extraction priority is:

1. homepage meta description
2. homepage Open Graph description
3. homepage H1/H2 text
4. About/contact paragraph text

The project does not generate marketing copy. It stores text found on the website wherever possible so the value represents the store's own wording.

## 11. Logo extraction

Favicon URLs are deliberately rejected.

Logo candidates are taken from:

1. JSON-LD `Organization.logo` / `Brand.logo`
2. images whose alt/class/id/src clearly indicate a logo

The final dataset stores a direct logo URL. The assignment permits either a logo URL or a saved image file, so saving large binary assets locally is not required.

## 12. State extraction

State identification prefers explicit Indian state names in the storefront content or JSON-LD address information.

The extractor includes Indian states and union territories listed in `app/config.py`.

State is left blank when the available evidence is insufficient rather than guessed.

## 13. Deduplication

Final records are deduplicated by normalized hostname.

Example variants that collapse to one store:

```text
https://example.com
https://www.example.com/
http://example.com/?utm_source=test
```

A custom domain that redirects from a `myshopify.com` candidate is represented using the final canonical URL.

## 14. Outputs

The pipeline creates:

```text
data/outputs/indian_shopify_stores.csv
```

The CSV contains exactly these seven required columns:

```text
domain_url
contacts
socials
category
tagline_description
logo
state
```

It also creates:

```text
data/outputs/audit.jsonl
data/outputs/run_summary.json
```

`audit.jsonl` contains verification evidence for every accepted store. `run_summary.json` contains field-completeness metrics.

## 15. Installation on Windows

### Step 1: Install Python

Python 3.12 is recommended for this assignment. Python 3.13+ can also work, but use a dedicated virtual environment.

Verify:

```powershell
python --version
```

### Step 2: Create the project folder

```powershell
mkdir rivyou-shopify-assignment
cd rivyou-shopify-assignment
```

### Step 3: Create a virtual environment

```powershell
python -m venv .venv
```

### Step 4: Activate it

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate
```

### Step 5: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Step 6: Install dependencies

```powershell
pip install -r requirements.txt
```

## 16. Run tests

```powershell
python -m pytest -q
```

The tests cover representative Shopify detection, India evidence, contact extraction, and social extraction cases.

## 17. Smoke test before a full run

Start with 20 candidates and disable Common Crawl:

```powershell
python run.py --limit 20 --no-common-crawl
```

This checks that:

- dependencies work
- networking works
- `robots.txt` handling works
- HTML extraction works
- CSV/JSON output is generated

Inspect:

```text
data/outputs/indian_shopify_stores.csv
data/outputs/audit.jsonl
data/outputs/run_summary.json
```

Then run a larger sample:

```powershell
python run.py --limit 200 --no-common-crawl
```

Finally run the full discovery pipeline:

```powershell
python run.py
```

## 18. Building toward 1,000+ verified stores

Do not claim 1,000+ until the output file actually contains at least 1,000 verified rows.

If the first full run is below the target:

1. add additional public seed URLs to `data/seeds.txt`
2. rerun discovery/verification
3. inspect rejected candidates in the console
4. check whether the shortage is caused by Shopify verification or India verification
5. expand the candidate source, not the acceptance criteria

The key rule is that increasing the count should come from better discovery, not by weakening verification.

## 19. Data-quality checks before submission

Open `run_summary.json` and record the actual values.

The final README should report the real run, for example:

```text
Candidates discovered: <actual value>
Verified Indian Shopify stores: <actual value>
Email present: <actual percentage>%
Phone present: <actual percentage>%
Socials present: <actual percentage>%
Logo present: <actual percentage>%
State present: <actual percentage>%
Unknown category: <actual percentage>%
```

Do not replace the placeholders with estimated numbers.

## 20. Known limitations

### JavaScript-heavy storefronts

The core crawler uses direct HTTP requests and HTML parsing. Stores that render most important content only after client-side JavaScript may expose fewer fields.

### State ambiguity

A store that mentions several states or serves all of India may not expose a clear business state. In ambiguous cases the pipeline leaves the state blank.

### Contact information

Some merchants intentionally publish no phone number or email. Missing contact values are therefore possible.

### Discovery coverage

Common Crawl and public seed lists are snapshots, not authoritative registries. Some live Shopify stores will not be present in a particular crawl.

### Scale

At 10x-100x scale, a production version should move crawling to a distributed queue, persist intermediate results, add stronger retry/backoff controls, and use a more comprehensive domain discovery system.

## 21. Assumptions

- "India-based" means the storefront exposes evidence of an Indian business location, not merely Indian customers or shipping availability.
- A custom domain is preferred over a `myshopify.com` domain when redirects reveal the custom domain.
- A missing field is acceptable when the site does not publish that information.
- The pipeline does not invent category, contact, state, or description values.
- The final dataset is generated from live verification after candidate discovery.
- All website crawling is subject to `robots.txt`, timeouts, and request-rate limits.

## 23. Runtime

Record the actual wall-clock time for the final run and put it here before submission.

```text
Candidate limit: 3,000
Common Crawl: disabled
Max workers: 15
Total runtime: 3,607.34 seconds (60.12 minutes)
```
