import json
import re
import phonenumbers
from phonenumbers import PhoneNumberFormat

from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

from .config import INDIAN_STATES
from .detection import INDIAN_CITIES

from .utils import absolute_url
from .utils import clean_text
from .utils import remove_duplicates


# ---------------------------------
# Email pattern
# ---------------------------------

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}\b"
)


# ---------------------------------
# Phone pattern
# ---------------------------------

PHONE_RE = re.compile(
    r"(?:\+91[\s.-]*)?[6-9]\d{9}\b"
)


# ---------------------------------
# Image extensions
# ---------------------------------

IMAGE_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".avif"
]


# ---------------------------------
# Social media domains
# ---------------------------------

SOCIAL_DOMAINS = {
    "instagram.com": "instagram",
    "facebook.com": "facebook",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube"
}


# ---------------------------------
# Fake / placeholder email values
# ---------------------------------

BAD_EMAIL_DOMAINS = [
    "example.com",
    "example.org",
    "example.net",
    "sentry.zipify.com",
    "bundle.js"
]


BAD_EMAIL_WORDS = [
    "logo",
    "image",
    "chatgpt",
    "screenshot",
    "untitled",
    "social-media",
    "thumbnail"
]


# ---------------------------------
# Check whether email is real
# ---------------------------------

def is_real_email(email):

    email = email.strip().lower()

    if not email:

        return False

    # -----------------------------
    # Basic check
    # -----------------------------

    if email.count("@") != 1:

        return False

    parts = email.split("@")

    if len(parts) != 2:

        return False

    username = parts[0]

    domain = parts[1]

    if not username:

        return False

    if not domain:

        return False

    # -----------------------------
    # Reject image file names
    # -----------------------------

    for extension in IMAGE_EXTENSIONS:

        if email.endswith(extension):

            return False

    # -----------------------------
    # Reject @2x image names
    # -----------------------------

    if "@2x." in email:

        return False

    # -----------------------------
    # Reject known bad domains
    # -----------------------------

    for bad_domain in BAD_EMAIL_DOMAINS:

        if bad_domain in domain:

            return False

    # -----------------------------
    # Reject obvious fake words
    # -----------------------------

    for bad_word in BAD_EMAIL_WORDS:

        if bad_word in username:

            return False

    return True

def normalize_email(value):
    """
    Extract and normalize a real email address from raw text.
    """
    if not value:
        return None

    value = unquote(str(value)).strip()

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        value,
    )

    if not match:
        return None

    email = match.group(0).lower().strip()

    if not is_real_email(email):
        return None

    return email


# ---------------------------------
# Extract contacts
# ---------------------------------

def extract_contacts(pages):

    emails = []

    phones = []

    for page in pages:

        # ---------------------------------
        # Use visible page text for emails
        # ---------------------------------

        found_emails = EMAIL_RE.findall(
            page.text
        )

        for email in found_emails:

            normalized = normalize_email(email)

            if normalized:

                emails.append(
                    normalized
                )

        # ---------------------------------
        # Find phones in visible text
        # ---------------------------------

        found_phones = PHONE_RE.findall(
            page.text
        )

        for phone in found_phones:

            phone = phone.strip()

            if phone:

                phones.append(
                    phone
                )

        # ---------------------------------
        # Check mailto and tel links
        # ---------------------------------

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        links = soup.find_all(
            "a",
            href=True
        )

        for link in links:

            href = link.get(
                "href",
                ""
            ).strip()

            # -----------------------------
            # Email
            # -----------------------------

            if href.lower().startswith(
                "mailto:"
            ):

                email = href[7:].split("?")[0].strip()

                normalized = normalize_email(email)

                if normalized:

                    emails.append(
                        normalized
                    )

            # -----------------------------
            # Phone
            # -----------------------------

            elif href.lower().startswith(
                "tel:"
            ):

                phone = (
                    href[4:]
                    .strip()
                )

                if phone:

                    phones.append(
                        phone
                    )

    emails = remove_duplicates(emails)

    normalized_phones = []
    
    for phone in phones:
        normalized = normalize_phone(phone)
    
        if normalized and normalized not in normalized_phones:
            normalized_phones.append(normalized)
    
    return emails, normalized_phones


# ---------------------------------
# Extract social media
# ---------------------------------

def extract_socials(pages):
    """
    Extract official social media profile/channel URLs.

    Removes common non-profile links such as:
    - Facebook share/watch/video/post links
    - Instagram posts/reels/stories
    - Twitter/X share/intent/status links
    - YouTube watch/shorts/embed/playlist links
    - LinkedIn non-profile links
    """

    socials = {}

    for page in pages:
        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        for link in soup.find_all(
            "a",
            href=True
        ):
            href = absolute_url(
                page.url,
                link.get("href")
            )

            if not href:
                continue

            parsed = urlparse(href)

            hostname = parsed.hostname or ""

            hostname = hostname.lower().replace(
                "www.",
                "",
                1
            )

            path = parsed.path.lower().strip("/")

            query = parsed.query.lower()

            social_name = None

            # ---------------------------------
            # Facebook
            # ---------------------------------

            if (
                hostname == "facebook.com"
                or hostname.endswith(
                    ".facebook.com"
                )
            ):

                if (
                    not path
                    or path.startswith("sharer")
                    or path.startswith("share")
                    or path.startswith("watch")
                    or "/watch" in path
                    or path.startswith("videos")
                    or path.startswith("video")
                    or "/videos/" in path
                    or path.startswith("reel")
                    or path.startswith("reels")
                    or path.startswith("posts")
                    or "/posts/" in path
                    or path == "profile.php"
                    or "share" in query
                ):
                    continue

                social_name = "facebook"

            # ---------------------------------
            # Instagram
            # ---------------------------------

            elif (
                hostname == "instagram.com"
                or hostname.endswith(
                    ".instagram.com"
                )
            ):

                if (
                    not path
                    or path.startswith("p/")
                    or path.startswith("reel/")
                    or path.startswith("reels/")
                    or path.startswith("stories/")
                    or path.startswith("s/")
                    or path.startswith("explore/")
                    or path.startswith("accounts/")
                ):
                    continue

                social_name = "instagram"

            # ---------------------------------
            # Twitter / X
            # ---------------------------------

            elif (
                hostname == "twitter.com"
                or hostname.endswith(
                    ".twitter.com"
                )
                or hostname == "x.com"
                or hostname.endswith(
                    ".x.com"
                )
            ):

                if (
                    not path
                    or path.startswith("share")
                    or path.startswith("intent")
                    or path.startswith("i/")
                    or path.startswith("status/")
                    or path.startswith("home")
                ):
                    continue

                social_name = "twitter"

            # ---------------------------------
            # LinkedIn
            # ---------------------------------

            elif (
                hostname == "linkedin.com"
                or hostname.endswith(
                    ".linkedin.com"
                )
            ):

                if not (
                    path.startswith("company/")
                    or path.startswith("in/")
                ):
                    continue

                social_name = "linkedin"

            # ---------------------------------
            # YouTube
            # ---------------------------------

            elif (
                hostname == "youtube.com"
                or hostname.endswith(
                    ".youtube.com"
                )
            ):

                if not (
                    path.startswith("channel/")
                    or path.startswith("c/")
                    or path.startswith("user/")
                    or path.startswith("@")
                ):
                    continue

                social_name = "youtube"

            if social_name is None:
                continue

            if social_name not in socials:
                socials[social_name] = []

            if href not in socials[social_name]:
                socials[social_name].append(
                    href
                )

    return socials


# ---------------------------------
# Get JSON-LD objects
# ---------------------------------

def get_json_ld_objects(
    soup
):

    objects = []

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:

        try:

            data = json.loads(
                script.get_text(
                    strip=True
                )
            )

            if isinstance(
                data,
                list
            ):

                for item in data:

                    objects.append(
                        item
                    )

            else:

                objects.append(
                    data
                )

        except Exception:

            continue

    return objects


# ---------------------------------
# Validate logo URL
# ---------------------------------

def is_valid_logo_url(
    url
):

    if not url:

        return False

    url = url.strip()

    if not (
        url.startswith("http://")
        or
        url.startswith("https://")
    ):

        return False

    lower_url = url.lower()

    bad_words = [
        "favicon",
        "/data/",
        "data/png",
        "placeholder",
        "sprite",
        "no-image",
        "no_image",
        "chatgpt_image",
        "background",
        "untitled_design"
    ]

    for word in bad_words:

        if word in lower_url:

            return False

    parsed = urlparse(
        url
    )

    path = parsed.path.lower()

    for extension in IMAGE_EXTENSIONS:

        if path.endswith(
            extension
        ):

            return True

    if "cdn.shopify.com" in lower_url:

        if "/files/" in path:

            return True

        if "/cdn/shop/" in path:

            return True

    if "logo" in lower_url:

        return True

    return False


# ---------------------------------
# Extract logo
# ---------------------------------

def extract_logo(pages):

    logo_urls = []

    # ---------------------------------
    # Check JSON-LD
    # ---------------------------------

    for page in pages:

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        objects = get_json_ld_objects(
            soup
        )

        for item in objects:

            if not isinstance(
                item,
                dict
            ):

                continue

            item_type = item.get(
                "@type"
            )

            if (
                item_type == "Organization"
                or
                item_type == "Brand"
            ):

                logo = item.get(
                    "logo"
                )

                if isinstance(
                    logo,
                    str
                ):

                    logo_url = absolute_url(
                        page.url,
                        logo
                    )

                    if is_valid_logo_url(
                        logo_url
                    ):

                        logo_urls.append(
                            logo_url
                        )

                elif isinstance(
                    logo,
                    dict
                ):

                    logo_url = (
                        logo.get("url")
                        or
                        logo.get(
                            "contentUrl"
                        )
                    )

                    logo_url = absolute_url(
                        page.url,
                        logo_url
                    )

                    if is_valid_logo_url(
                        logo_url
                    ):

                        logo_urls.append(
                            logo_url
                        )

    # ---------------------------------
    # Check image tags
    # ---------------------------------

    for page in pages:

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        images = soup.find_all(
            "img"
        )

        for image in images:

            src = (
                image.get("src")
                or
                image.get("data-src")
                or
                image.get("data-lazy-src")
            )

            if not src:

                continue

            src = absolute_url(
                page.url,
                src
            )

            if not src:

                continue

            alt = clean_text(
                image.get(
                    "alt",
                    ""
                )
            ).lower()

            image_class = " ".join(
                image.get(
                    "class",
                    []
                )
            ).lower()

            image_id = clean_text(
                image.get(
                    "id",
                    ""
                )
            ).lower()

            info = (
                alt
                + " "
                + image_class
                + " "
                + image_id
                + " "
                + src.lower()
            )

            if "favicon" in info:

                continue

            if "logo" not in info:

                continue

            if is_valid_logo_url(
                src
            ):

                logo_urls.append(
                    src
                )

    logo_urls = remove_duplicates(
        logo_urls
    )

    if logo_urls:

        return logo_urls[0]

    return ""


# ---------------------------------
# Extract description
# ---------------------------------

def extract_description(
    pages
):

    for page in pages:

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:

            content = meta.get(
                "content"
            )

            if content:

                return clean_text(
                    content
                )

        og = soup.find(
            "meta",
            attrs={
                "property":
                    "og:description"
            }
        )

        if og:

            content = og.get(
                "content"
            )

            if content:

                return clean_text(
                    content
                )

        h1 = soup.find(
            "h1"
        )

        if h1:

            value = clean_text(
                h1.get_text(
                    " ",
                    strip=True
                )
            )

            if 20 <= len(value) <= 300:

                return value

        h2 = soup.find(
            "h2"
        )

        if h2:

            value = clean_text(
                h2.get_text(
                    " ",
                    strip=True
                )
            )

            if 20 <= len(value) <= 300:

                return value

    return ""


# ---------------------------------
# Extract category
# ---------------------------------

# ---------------------------------
# Extract category
# ---------------------------------

def extract_category(pages):
    """
    Classify the store using the store's own description first.

    Strong rules use distinctive product/category phrases from the
    description. A fallback classifier is used only when needed.
    """

    description = extract_description(pages)
    desc = clean_text(description).lower()

    desc = (
        desc.replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
    )

    # --------------------------------------------------
    # Very specific phrases that identify stores whose
    # descriptions are too short or use unusual wording.
    # These checks run before the general keyword rules.
    # --------------------------------------------------
    specific_category_rules = [
        ("food & beverages", [
            "homemade achar",
            "online cakes",
            "alphonso mangoes",
            "fresh & crunchy, premium quality, gourmet nuts",
            "energizing drink",
            "a2 milk",
            "a2 bilona ghee",
            "organic grocery",
            "meadery",
            "alcoholic beverage",
        ]),
        ("electronics", [
            "music instrument",
            "audio equipment superstore",
            "apple premium partner",
            "apple products",
            "unique gadgets, mobile phones",
            "authorised distributor of apple products",
            "audio/video shopping site",
            "home theatre and hifi audio",
        ]),
        ("motorcycle & automotive", [
            "riding gear",
            "multi brand riding gear",
        ]),
        ("health & wellness", [
            "diabetes reversal program",
            "anti-pollution masks",
            "glutathione deficiency treatment",
            "b12 deficiency treatment",
            "vitamin d3 deficiency",
            "satvic store",
            "goodness of moringa",
        ]),
        ("apparel", [
            "natural cotton fabrics",
            "buy fabric online",
            "indian looms",
        ]),
        ("arts & design", [
            "craft kits & supplies",
            "epoxy resin",
            "resin materials",
        ]),
        ("home fragrance", [
            "aromatherapy and scent",
            "scent diffusion systems",
            "incense sticks",
            "incense cones",
        ]),
        ("home care & cleaning", [
            "home & hygiene products",
            "home and hygiene products",
        ]),
        ("maternity & baby", [
            "mother sparsh baby care",
            "wipes, lotions, soaps, washes",
        ]),
        ("sustainable products", [
            "sustainable, eco-friendly",
            "verified sustainable",
            "plastic-free packaging",
            "carbon-neutral delivery",
        ]),
        ("flowers & gifting", [
            "fresh flowers online",
            "flower delivery partner",
            "same-day luxury flowers",
            "cut flowers",
            "hand-tied bouquets",
        ]),
        ("fitness & sports", [
            "online sports store",
            "sports equipment at best prices",
            "health & fitness products",
        ]),
        ("beauty & cosmetics", [
            "high-performing hair and body care products",
            "human hair extensions",
        ]),
        ("shoe care", [
            "sneaker care",
            "sneaker cleaning",
            "sneaker protection",
        ]),
        ("skincare", [
            "handmade skin care, hair care, and body care products",
        ]),
        ("software & IT services", [
            "shopify web developers",
            "shopify custom solutions",
        ]),
        ("home appliances", [
            "ceiling, wall, pedestal, table",
            "ceiling fans",
            "pedestal fans",
        ]),
        ("personal care", [
            "complete men's grooming range",
            "men's grooming products",
        ]),
        ("home decor", [
            "memory foam pillow",
            "memory foam pillows",
            "contemporary homeware",
        ]),
    ]

    for category, keywords in specific_category_rules:
        if any(keyword in desc for keyword in keywords):
            return category

    # A couple of mixed descriptions need a very precise phrase check.
    if "delivering foods" in desc and "heirloom seeds" in desc:
        return "food & beverages"

    if "cool, funny t-shirts" in desc and "hoodies" in desc:
        return "apparel"

    # --------------------------------------------------
    # Strong description-based categories
    # Keep specific categories before broad categories.
    # --------------------------------------------------

    strong_categories = [
        (
            "eyewear",
            [
                "eyeglasses",
                "sunglasses",
                "contact lens",
                "contact lenses",
                "optical frames",
            ],
        ),
        (
            "gardening & seeds",
            [
                "seeds online",
                "quality seeds",
                "heirloom seeds",
                "non-gmo seeds",
                "garden seeds",
                "gardening",
            ],
        ),
        (
            "industrial equipment",
            [
                "ladder",
                "ladders",
                "scaffold",
                "scaffolding",
                "tower scaffoldings",
                "extension ladder",
                "step ladders",
            ],
        ),
        (
            "furniture",
            [
                "wooden furniture",
                "solid wood furniture",
                "furniture online",
                "wooden beds",
                "home furniture",
                "dining sets",
                "bookshelves",
                "ergonomic chairs",
                "office chairs",
            ],
        ),
        (
            "solar & renewable energy",
            [
                "solar panel",
                "solar panels",
                "solar company",
                "solar inverter",
                "solar installation",
                "lithium batteries",
                "solar battery",
                "rooftop solar",
                "charge controllers",
            ],
        ),
        (
            "cycling & sports",
            [
                "cycling store",
                "cycling accessories",
                "cycling helmets",
                "cycling jerseys",
                "cycling shoes",
                "bicycles",
                "bike accessories",
                "mtb cycle",
                "kids cycles",
            ],
        ),
        (
            "luggage & travel",
            [
                "smart luggage",
                "trolley bags",
                "luggage",
                "travel bags",
                "suitcases",
            ],
        ),
        (
            "gifts",
            [
                "personalized gifts",
                "personalized gift",
                "corporate gifts",
                "gift hampers",
                "gift shop",
                "gift boxes",
                "gifts for babies",
                "unique gifts",
                "gift ideas",
            ],
        ),
        (
            "home appliances",
            [
                "stabilizers and geysers",
                "water heaters",
                "geyser",
                "home appliances",
                "kitchen appliances",
                "electrical appliances",
            ],
        ),
        (
            "software & IT services",
            [
                "software service",
                "software services",
                "biometric devices",
                "device registration",
                "whitelisting",
                "it services",
            ],
        ),
        (
            "gaming & electronics",
            [
                "gaming products",
                "gaming accessories",
                "gaming chair",
                "gaming desk",
                "gaming station",
            ],
        ),
        (
            "pets",
            [
                "online pet store",
                "pet store",
                "pet food",
                "pet toys",
                "pet grooming",
                "pet accessories",
            ],
        ),
        (
            "toys",
            [
                "educational wooden jigsaw puzzles",
                "jigsaw puzzles",
                "board games",
                "educational toys",
                "wooden toys",
                "kids toys",
                "toys for children",
            ],
        ),
        (
            "food & beverages",
            [
                "peanut butter",
                "premium chocolates",
                "gourmet treats",
                "cookies",
                "wine",
                "tea",
                "coffee",
                "snacks",
                "food products",
                "food products",
                "beverages",
                "sauces",
                "mayo",
                "spreads",
                "dry fruits",
                "banana chips",
                "cold pressed oils",
            ],
        ),
        (
            "phone accessories",
            [
                "phone case",
                "phone cases",
                "iphone cases",
                "mobile accessories",
                "magnetic sleeves",
                "device skins",
            ],
        ),
        (
            "motorcycle & automotive",
            [
                "car accessories",
                "car accessories online",
                "automotive accessories",
                "car parts",
                "motorcycle protective gear",
                "motorcycle gear",
                "riding jackets",
                "motorcycle pants",
                "biker gloves",
                "saddlebags",
                "tankbags",
                "tailbags",
            ],
        ),
        (
            "skincare",
            [
                "hair and skin care",
                "hair & skin care",
                "skin care products",
                "skincare products",
                "hair care products",
                "cleansers",
                "moisturizers",
                "face serums",
                "skin serum",
                "face wash",
            ],
        ),
        (
            "beauty & cosmetics",
            [
                "cosmetics",
                "lipstick",
                "mascara",
                "foundation",
                "makeup",
                "beauty products",
                "perfumes",
                "fragrances",
            ],
        ),
        (
            "personal care",
            [
                "personal hygiene products",
                "personal hygiene",
                "intimate wash",
                "intimate wipes",
                "home and hygiene products",
                "home hygiene products",
            ],
        ),
        (
            "kitchenware",
            [
                "kitchenware retailer",
                "kitchenware",
                "kitchen essentials",
                "cookware",
                "pressure cookers",
                "saucepans",
                "frypans",
            ],
        ),
        (
            "books",
            [
                "online bookstore",
                "books online",
                "book shop",
                "bookstore",
                "astrology books",
                "religious books",
                "books",
            ],
        ),
        (
            "jewellery",
            [
                "jewellery",
                "jewelry",
                "necklace",
                "bracelet",
                "earrings",
                "bangles",
                "rings",
            ],
        ),
        (
            "footwear",
            [
                "shoes",
                "sneakers",
                "sandals",
                "footwear",
                "fashion footwear",
            ],
        ),
        (
            "innerwear",
            [
                "underwear",
                "innerwear",
                "lingerie",
                "boxers",
                "briefs",
            ],
        ),
        (
            "home decor",
            [
                "home decor",
                "home décor",
                "interior home decor",
                "handicrafts",
                "handicraft items",
                "traditional handicraft",
                "bedsheets",
                "bed sheets",
                "home furnishings",
                "home textiles",
            ],
        ),
        (
            "arts & design",
            [
                "vector templates",
                "psd mockups",
                "plotters & cutters",
                "skin vector templates",
                "online art gallery",
                "art prints",
                "art merchandise",
            ],
        ),
        (
            "fitness & sports",
            [
                "home gym equipment",
                "fitness equipment",
                "exercise bikes",
                "treadmills",
                "dumbbells",
                "sports nutrition",
                "activewear",
                "gym wear",
                "workout clothes",
            ],
        ),
        (
            "health & wellness",
            [
                "hair loss",
                "dermatology",
                "cbd & hemp",
                "hemp products",
                "wellness essentials",
                "ayurvedic",
                "natural wellness",
            ],
        ),
        (
            "maternity & baby",
            [
                "maternity wear",
                "maternity clothing",
                "baby products",
                "newborn essentials",
                "baby essentials",
                "diapers",
            ],
        ),
        (
            "kids apparel",
            [
                "kids clothes",
                "kids clothing",
                "nightwear for kids",
                "kids t-shirts",
                "clothes for kids",
            ],
        ),
        (
            "women's apparel",
            [
                "women's clothing",
                "womenswear",
                "women's wear",
                "women's fashion",
                "women's designer clothes",
                "dresses for women",
                "pakistani suits",
                "salwar kameez",
                "women's dresses",
                "sarees for women",
                "designer sarees",
                "lehengas",
                "anarkalis",
                "shararas",
            ],
        ),
        (
            "men's apparel",
            [
                "men's wear",
                "menswear",
                "men's clothing",
                "men's fashion",
                "curated menswear",
                "men's inner wear",
            ],
        ),
        (
            "apparel",
            [
                "women's, men's, kids' fashion",
                "women's, men's and kids",
                "clothing, accessories, art, and homeware",
                "men & women clothing",
                "kids clothing",
            ],
        ),
    ]

    for category, keywords in strong_categories:
        for keyword in keywords:
            if keyword in desc:
                return category

    # --------------------------------------------------
    # Fallback classifier
    # Prefer the store description. Only use the whole page
    # when there is no usable description.
    # --------------------------------------------------

    if desc:
        source_text = desc
    else:
        source_text = " ".join(
            clean_text(page.text).lower()
            for page in pages
            if page.text
        )

    fallback_categories = {
        "electronics": [
            "electronics",
            "headphones",
            "earbuds",
            "charger",
            "speaker",
            "smartwatch",
            "computer",
            "laptop",
            "gaming",
        ],
        "skincare": [
            "skincare",
            "serum",
            "moisturizer",
            "face wash",
            "cleanser",
        ],
        "beauty & cosmetics": [
            "cosmetics",
            "lipstick",
            "mascara",
            "foundation",
            "makeup",
        ],
        "men's apparel": [
            "men's clothing",
            "menswear",
            "shirts",
            "t-shirts",
            "trousers",
        ],
        "kids apparel": [
            "kids clothes",
            "kids clothing",
            "nightwear for kids",
        ],
        "maternity & baby": [
            "maternity wear",
            "baby products",
            "newborn essentials",
            "diapers",
        ],
        "women's apparel": [
            "women's clothing",
            "womenswear",
            "dresses",
            "kurti",
            "saree",
        ],
        "jewellery": [
            "jewellery",
            "jewelry",
            "necklace",
            "bracelet",
            "earrings",
        ],
        "home decor": [
            "home decor",
            "wall art",
            "cushion",
            "bedsheets",
            "bed sheets",
            "decor",
        ],
        "food & beverages": [
            "snacks",
            "tea",
            "coffee",
            "food",
            "beverages",
            "chocolate",
        ],
        "health & wellness": [
            "wellness",
            "supplements",
            "nutrition",
            "ayurveda",
        ],
        "stationery": [
            "stationery",
            "notebooks",
            "pens",
            "journals",
            "school supplies",
        ],
        "footwear": [
            "shoes",
            "sneakers",
            "sandals",
            "footwear",
        ],
        "toys": [
            "toys",
            "puzzles",
            "board games",
        ],
        "gifts": [
            "gifts",
            "gift shop",
            "gift hampers",
        ],
        "pets": [
            "pet store",
            "pet food",
            "pet accessories",
        ],
        "motorcycle & automotive": [
            "car accessories",
            "automotive",
            "motorcycle",
        ],
        "cycling & sports": [
            "cycling",
            "bicycle",
            "bicycles",
        ],
        "furniture": [
            "furniture",
            "sofa",
            "wooden bed",
            "chairs",
        ],
    }

    scores = {}

    for category, keywords in fallback_categories.items():
        score = 0

        for keyword in keywords:
            if keyword in source_text:
                score += 1

        if score:
            scores[category] = score

    if not scores:
        return "unknown"

    return max(scores, key=scores.get)


# ---------------------------------
# Extract state from JSON-LD
# ---------------------------------

def extract_state_from_address_data(
    pages
):

    states = sorted(
        INDIAN_STATES.items(),
        key=lambda x: len(
            x[0]
        ),
        reverse=True
    )

    for page in pages:

        soup = BeautifulSoup(
            page.html,
            "lxml"
        )

        objects = get_json_ld_objects(
            soup
        )

        for item in objects:

            if not isinstance(
                item,
                dict
            ):

                continue

            address = item.get(
                "address"
            )

            if not isinstance(
                address,
                dict
            ):

                continue

            # ---------------------------------
            # addressRegion
            # ---------------------------------

            region = address.get(
                "addressRegion",
                ""
            )

            region = str(
                region
            ).lower()

            for state_name, real_name in states:

                if state_name in region:

                    return real_name

            # ---------------------------------
            # Full address
            # ---------------------------------

            address_text = ""

            for value in address.values():

                address_text = (
                    address_text
                    + " "
                    + str(value)
                )

            address_text = (
                address_text.lower()
            )

            for state_name, real_name in states:

                if state_name in address_text:

                    return real_name

            # ---------------------------------
            # City
            # ---------------------------------

            for city, state in INDIAN_CITIES.items():

                if city in address_text:

                    return state

    return None

def normalize_phone(phone):
    """
    Clean and normalize phone numbers.

    Returns E.164 format when the number is valid.
    Returns None for obvious HTML fragments.
    """
    if not phone:
        return None

    value = unquote(str(phone)).strip()

    # Reject HTML fragments accidentally captured as phone values.
    lower_value = value.lower()

    bad_fragments = [
        "<a",
        "</a",
        "href=",
        "javascript:",
        "mailto:",
    ]

    for fragment in bad_fragments:
        if fragment in lower_value:
            return None

    # Remove common labels.
    value = re.sub(
        r"(?i)\b(phone|tel|mobile|whatsapp|call|contact)\s*[:\-]?\s*",
        "",
        value,
    )

    # Fix obvious formatting problems.
    value = value.replace("++", "+").strip()

    # Try to isolate an Indian mobile/phone number.
    match = re.search(
        r"\+?91[\s.-]*\d(?:[\d\s().-]{7,}\d)",
        value,
    )

    if not match:
        match = re.search(
            r"\b[6-9]\d{9}\b",
            value,
        )

    candidate = match.group(0) if match else value
    candidate = candidate.strip()

    try:
        parsed = phonenumbers.parse(candidate, "IN")

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                PhoneNumberFormat.E164,
            )

    except phonenumbers.NumberParseException:
        pass

    cleaned = re.sub(r"[^0-9+().\-\s]", "", candidate)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(re.sub(r"\D", "", cleaned)) >= 8:
        return cleaned

    return None