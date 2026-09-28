import re

from .config import INDIAN_STATES
from .config import MIN_INDIA_SCORE
from .config import MIN_SHOPIFY_SCORE

from .utils import clean_text


# ---------------------------------
# Shopify detection signals
# ---------------------------------

SHOPIFY_SIGNALS = {

    "cdn.shopify.com": 3,

    "window.shopify": 3,

    "shopify.theme": 3,

    "shopify.routes": 2,

    "shopify-section": 2,

    "shopify-payment-button": 2,

    "/cdn/shop/": 2,
}


# ---------------------------------
# Indian GST number
# ---------------------------------

GSTIN_RE = re.compile(
    r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
    re.I
)


# ---------------------------------
# Indian phone number
# ---------------------------------

PHONE_RE = re.compile(
    r"(?:\+91[\s.-]*)?[6-9]\d{9}\b"
)


# ---------------------------------
# Indian PIN code
# ---------------------------------

PINCODE_RE = re.compile(
    r"\b[1-9][0-9]{5}\b"
)


# ---------------------------------
# Common Indian cities
# ---------------------------------

INDIAN_CITIES = {

    "mumbai": "Maharashtra",

    "pune": "Maharashtra",

    "nagpur": "Maharashtra",

    "delhi": "Delhi",

    "new delhi": "Delhi",

    "hyderabad": "Telangana",

    "secunderabad": "Telangana",

    "bangalore": "Karnataka",

    "bengaluru": "Karnataka",

    "mysore": "Karnataka",

    "chennai": "Tamil Nadu",

    "coimbatore": "Tamil Nadu",

    "madurai": "Tamil Nadu",

    "ahmedabad": "Gujarat",

    "surat": "Gujarat",

    "vadodara": "Gujarat",

    "kolkata": "West Bengal",

    "jaipur": "Rajasthan",

    "udaipur": "Rajasthan",

    "lucknow": "Uttar Pradesh",

    "kanpur": "Uttar Pradesh",

    "noida": "Uttar Pradesh",

    "gurugram": "Haryana",

    "gurgaon": "Haryana",

    "faridabad": "Haryana",

    "chandigarh": "Chandigarh",

    "kochi": "Kerala",

    "ernakulam": "Kerala",

    "bhubaneswar": "Odisha",

    "patna": "Bihar",

    "indore": "Madhya Pradesh",

    "bhopal": "Madhya Pradesh",

    "visakhapatnam": "Andhra Pradesh",

    "vizag": "Andhra Pradesh",

    "vijayawada": "Andhra Pradesh",

    "tirupati": "Andhra Pradesh",

    "ranchi": "Jharkhand",

    "guwahati": "Assam"
}


# ---------------------------------
# Detect Shopify
# ---------------------------------

def detect_shopify(html, host):

    html = html or ""

    html = html.lower()

    score = 0

    signals = []

    for signal in SHOPIFY_SIGNALS:

        if signal in html:

            score = (
                score
                + SHOPIFY_SIGNALS[signal]
            )

            signals.append(
                signal
            )

    # myshopify.com is a strong signal

    if host.endswith(
        ".myshopify.com"
    ):

        score = score + 4

        signals.append(
            "myshopify.com-hostname"
        )

    if score >= MIN_SHOPIFY_SCORE:

        return (
            True,
            score,
            signals
        )

    return (
        False,
        score,
        signals
    )


# ---------------------------------
# Extract Indian state
# ---------------------------------

def extract_state(text):

    text = clean_text(
        text
    )

    text_lower = text.lower()

    # ---------------------------------
    # Check full state names
    # ---------------------------------

    states = sorted(
        INDIAN_STATES.items(),
        key=lambda item: len(
            item[0]
        ),
        reverse=True
    )

    location_words = [

        "address",

        "contact",

        "office",

        "registered",

        "head office",

        "located",

        "location",

        "india",

        "pincode",

        "pin code",

        "postal"
    ]

    for state_name, real_name in states:

        position = text_lower.find(
            state_name
        )

        if position == -1:

            continue

        context_start = max(
            0,
            position - 120
        )

        context_end = min(
            len(text_lower),
            position + 120
        )

        context = text_lower[
            context_start:context_end
        ]

        for word in location_words:

            if word in context:

                return real_name

    # ---------------------------------
    # Check Indian cities
    # ---------------------------------

    for city, state in INDIAN_CITIES.items():

        position = text_lower.find(
            city
        )

        if position == -1:

            continue

        context_start = max(
            0,
            position - 100
        )

        context_end = min(
            len(text_lower),
            position + 100
        )

        context = text_lower[
            context_start:context_end
        ]

        for word in location_words:

            if word in context:

                return state

    return None


# ---------------------------------
# Detect whether store is Indian
# ---------------------------------

def detect_india(
    text,
    domain,
    state
):

    text = text or ""

    text = clean_text(
        text
    )

    lower_text = text.lower()

    score = 0

    evidence = []

    # ---------------------------------
    # India / Bharat
    # ---------------------------------

    if "india" in lower_text:

        score += 5

        evidence.append(
            "explicit_india"
        )

    elif "bharat" in lower_text:

        score += 5

        evidence.append(
            "explicit_india"
        )

    # ---------------------------------
    # State
    # ---------------------------------

    if state:

        score += 5

        evidence.append(
            "state:" + state
        )

    # ---------------------------------
    # GSTIN
    # ---------------------------------

    if GSTIN_RE.search(text):

        score += 6

        evidence.append(
            "gstin"
        )

    # ---------------------------------
    # Indian phone
    # ---------------------------------

    if PHONE_RE.search(text):

        score += 3

        evidence.append(
            "indian_phone"
        )

    # ---------------------------------
    # Indian PIN code
    # ---------------------------------

    if PINCODE_RE.search(text):

        score += 2

        evidence.append(
            "indian_pincode"
        )

    # ---------------------------------
    # Indian city
    # ---------------------------------

    city_found = None

    for city in INDIAN_CITIES:

        if city in lower_text:

            city_found = city

            break

    if city_found:

        score += 3

        evidence.append(
            "indian_city:"
            + city_found
        )

    # ---------------------------------
    # INR / Rupee
    # ---------------------------------

    if "₹" in text:

        score += 2

        evidence.append(
            "inr_symbol"
        )

    elif "inr" in lower_text:

        score += 2

        evidence.append(
            "inr_currency"
        )

    # ---------------------------------
    # Indian domain
    # ---------------------------------

    if domain.endswith(
        ".co.in"
    ):

        score += 2

        evidence.append(
            ".co.in_domain"
        )

    elif domain.endswith(
        ".in"
    ):

        score += 1

        evidence.append(
            ".in_domain"
        )

    # ---------------------------------
    # Check strong evidence
    # ---------------------------------

    strong_evidence = False

    # GSTIN is very strong

    if "gstin" in evidence:

        strong_evidence = True

    # Indian phone is strong

    elif "indian_phone" in evidence:

        strong_evidence = True

    # State + another Indian signal

    elif (
        state
        and (
            "indian_pincode"
            in evidence
            or
            "inr_symbol"
            in evidence
            or
            "inr_currency"
            in evidence
            or
            ".in_domain"
            in evidence
            or
            ".co.in_domain"
            in evidence
        )
    ):

        strong_evidence = True

    # Indian city + another signal

    elif (
        city_found
        and (
            "inr_symbol"
            in evidence
            or
            "inr_currency"
            in evidence
            or
            ".in_domain"
            in evidence
            or
            ".co.in_domain"
            in evidence
        )
    ):

        strong_evidence = True

    # ---------------------------------
    # IMPORTANT:
    #
    # India + INR alone is NOT enough.
    #
    # We intentionally removed:
    #
    # India + Indian currency
    #
    # because this can accept stores that
    # only target Indian customers but are
    # not necessarily based in India.
    # ---------------------------------

    # India + Indian domain

    elif (
        "explicit_india"
        in evidence
        and (
            ".in_domain"
            in evidence
            or
            ".co.in_domain"
            in evidence
        )
    ):

        strong_evidence = True

    if (
        score >= MIN_INDIA_SCORE
        and strong_evidence
    ):

        return (
            True,
            score,
            evidence
        )

    return (
        False,
        score,
        evidence
    )


# ---------------------------------
# Run complete analysis
# ---------------------------------

def analyze(
    html,
    host,
    text
):

    shopify, shopify_score, shopify_signals = (
        detect_shopify(
            html,
            host
        )
    )

    state = extract_state(
        text
    )

    india, india_score, india_evidence = (
        detect_india(
            text,
            host,
            state
        )
    )

    result = {

        "shopify":
            shopify,

        "shopify_score":
            shopify_score,

        "shopify_signals":
            shopify_signals,

        "india":
            india,

        "india_score":
            india_score,

        "india_evidence":
            india_evidence,

        "state":
            state
    }

    return result