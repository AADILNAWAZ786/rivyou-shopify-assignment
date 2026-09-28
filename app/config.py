from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "outputs"
SEED_FILE = DATA_DIR / "seeds.txt"


USER_AGENT = "RivyouShopifyResearchBot/1.0"

REQUEST_TIMEOUT = (2, 4)
MAX_WORKERS = 15
MAX_HTML_SIZE = 512 * 1024

MAX_SITE_TIME = 15

MIN_SHOPIFY_SCORE = 4

MIN_INDIA_SCORE = 5


COMMON_CRAWL_ENABLED = True

COMMON_CRAWL_LIMIT_PER_QUERY = 300


PUBLIC_SEED_URL = (
    "https://raw.githubusercontent.com/TeamDukaan/performance/master/"
    "shopify%20stores%20-%20shopify.csv"
)


COMMON_CRAWL_PATTERNS = [
    "*.myshopify.com/*",
    "*.in/cdn/shop/*",
    "*.co.in/cdn/shop/*",
]


PAGES_TO_TRY = [
    "/",
    "/contact",
    "/contact-us",
    "/pages/contact",
    "/pages/contact-us",
    "/about",
    "/about-us",
    "/pages/about",
    "/pages/about-us",
    "/policies/privacy-policy",
    "/policies/terms-of-service",
]


INDIAN_STATES = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli and daman and diu":
        "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry",
}