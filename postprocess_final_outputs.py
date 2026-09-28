import csv
import json
from pathlib import Path

INPUT_CSV = Path("data/outputs/indian_shopify_stores.csv")
AUDIT_JSONL = Path("data/outputs/audit.jsonl")
OUTPUT_CSV = Path("data/outputs/indian_shopify_stores_cleaned.csv")

CITY_STATE = {
    "mumbai": "Maharashtra", "delhi": "Delhi", "bangalore": "Karnataka",
    "bengaluru": "Karnataka", "mysore": "Karnataka", "hyderabad": "Telangana",
    "secunderabad": "Telangana", "chennai": "Tamil Nadu", "noida": "Uttar Pradesh",
    "gurugram": "Haryana", "gurgaon": "Haryana", "pune": "Maharashtra",
    "ahmedabad": "Gujarat", "kolkata": "West Bengal", "ranchi": "Jharkhand",
    "surat": "Gujarat", "indore": "Madhya Pradesh", "chandigarh": "Chandigarh",
    "faridabad": "Haryana", "lucknow": "Uttar Pradesh", "vadodara": "Gujarat",
    "udaipur": "Rajasthan", "patna": "Bihar", "kochi": "Kerala",
    "kanpur": "Uttar Pradesh", "madurai": "Tamil Nadu",
    "bhubaneswar": "Odisha", "ernakulam": "Kerala", "nagpur": "Maharashtra",
    "coimbatore": "Tamil Nadu",
}

RULES = [
    ("hair & beauty care", ["lip care", "lip balm", "lip scrub", "lip gloss",
        "hair extensions", "human hair", "hair bonding", "hair colour",
        "hair styling", "hair products", "shampoo", "hair care"]),
    ("home fragrance", ["home fragrance", "scented soy candles", "scented candles",
        "room sprays", "reed diffusers", "scented sachets", "bakhoor",
        "attars", "attar", "fragrance brand", "room freshners", "car freshners"]),
    ("pet care", ["dog harness", "dog collar", "dog leash", "pet care products",
        "pet supply", "pet supplies", "pet accessories", "dog shampoo",
        "dog treats", "pet store"]),
    ("packaging", ["packaging supplies", "packaging solutions", "bakery boxes",
        "packaging boxes", "paper bags", "custom packaging"]),
    ("games & puzzles", ["chess pieces", "chess boards", "luxury chess sets",
        "chess sets", "funko collectibles", "collectibles"]),
    ("travel accessories", ["passport covers", "passport holders",
        "passport holder", "travel accessories", "travel organizer", "travel gear"]),
    ("home textiles", ["bedding sets", "comforters", "duvet covers", "blankets",
        "bed linen", "bed bath", "table linen", "bedsheet", "bed sheet",
        "sheets", "towels", "duvets", "home furnishing"]),
    ("sanitary & menstrual care", ["sanitary napkins", "sanitary pads",
        "menstrual", "period experience"]),
    ("rugs & carpets", ["rugs & carpets", "rugs and carpets", "rugs", "carpets"]),
    ("home care & cleaning", ["home cleaning", "cleaning products",
        "natural home cleaners", "insect repellents", "cleaning supplies",
        "home care", "home & hygiene", "home hygiene"]),
    ("women's apparel", ["dupattas", "dupattas online", "ethnic wear for women",
        "chanderi", "handwoven saris", "womens kurta", "women's kurta", "sarees",
        "saris", "lehenga", "anarkali", "palazzo", "bridal studio", "bridal"]),
    ("men's apparel", ["men's shawl", "mens shawl", "men's clothing", "menswear",
        "men's wear", "men's fashion"]),
    ("apparel", ["official jerseys", "fan gear", "sports merchandise",
        "uniforms for", "healthcare professional", "clothes", "clothing",
        "apparel", "fashion", "wear", "dresses", "shirts", "t-shirts",
        "jeans", "pants", "shorts", "socks"]),
    ("luggage & travel", ["passport", "travel bags", "trolley", "luggage", "suitcases"]),
    ("bags & accessories", ["women's bags", "handbags", "bags online",
        "handcrafted bags", "designer bags", "leather bags", "leather accessories",
        "wallets", "bags"]),
    ("food & beverages", ["healthy snack", "ghee", "mithai", "namkeen",
        "dairy products", "pickles", "podi", "snacking", "snacks", "ice pops",
        "dryfruits", "dry fruits", "nuts", "berries", "trail mixes", "pasta",
        "noodles", "honey", "spice extract", "frozen smoothie", "smoothies",
        "cakes", "cupcakes", "desserts", "meat", "chicken", "mutton",
        "non-alcoholic beer", "sauces", "ingredients", "matcha", "mint",
        "cocktail mixers", "cocktails", "protein powder", "fresh produce",
        "laddus", "ladoo", "jams and preserves", "food brand", "gummy", "oils",
        "fresh meat"]),
    ("security & access solutions", ["digital locks", "smart locks",
        "access solutions", "access control"]),
    ("software & IT services", ["shopify plus agency", "shopify web developers",
        "custom erp integrations", "online store development", "software solution",
        "business consulting", "e-commerce consultant", "ecommerce consultant",
        "digital marketing software", "shopify template", "it | pro audio",
        "it | pro video"]),
    ("sports & fitness", ["functional fitness superstore", "fitness mats",
        "gym accessories", "gym gear", "fitness accessories", "fitness and gym gear",
        "yoga", "athlete", "sportsperson", "fitness"]),
    ("bedding & sleep", ["mattresses", "sleep products", "pregnancy pillows",
        "body pillows", "sleep better", "latex mattress", "mattress brand"]),
    ("medical & dental", ["dental supplies", "dental healthcare",
        "air quality monitoring", "air purifiers", "n95", "n99 masks"]),
    ("industrial equipment", ["cnc machine tools", "motion control",
        "industrial automation", "stepper motors", "servo drives", "machine tools",
        "sewing machine parts", "smart lockers", "workplace automation"]),
    ("fabric & textiles", ["fabric stores", "fabric store", "fabrics", "pure silk",
        "linen", "banarasi brocade", "cotton fabrics", "yarn store",
        "silk yarn", "fiber", "wool shawls", "shawls"]),
    ("lighting", ["neon lights", "customised neon lights", "custom neon sign",
        "handcrafting lights", "lamps", "lanterns", "lighting"]),
    ("electronics", ["iphone", "ipad", "macbook", "airpods", "cameras",
        "camera stabilizers", "video cranes", "jibs", "camera sliders",
        "mirrorless cameras", "tripods", "microphones", "routers", "walkie-talkies",
        "wifi solutions", "gps trackers", "bluetooth trackers", "tv & monitor mounting",
        "flashlights", "searchlights", "inverter", "battery", "home ups", "netgear",
        "raspberry pi", "pro audio", "pro video", "home audio", "home theatre",
        "audio systems"]),
    ("home appliances", ["water purifiers", "water purifier", "water softeners",
        "shower filters", "kitchen and home appliance", "home appliance retailer",
        "sanitaryware", "wash basin", "toilets", "faucets", "tap",
        "bath accessories", "kitchen fittings", "robotic vacuum cleaners"]),
    ("jewellery", ["rudraksha", "diamond", "lab grown diamond", "necklace",
        "jewelry", "jewellery", "gemstones"]),
    ("watches", ["watches for men", "watches for women", "premium timepieces", "watch"]),
    ("arts & design", ["design studio", "art studio", "paintings",
        "painting artwork", "photo frames", "art prints", "artisanal products",
        "art & diy craft", "craft & hobby supplies", "creative wonderland",
        "collectible design gallery", "artistic experiences"]),
    ("spiritual & religious", ["pooja mandir", "pooja temple", "marble idols",
        "hindu gods", "sanatan dharma", "vedic sahitya", "gurukul",
        "reiki crystal", "healing crystals"]),
    ("home decor", ["homeware", "home goods", "home & lifestyle",
        "home and lifestyle", "home & office", "plants", "nature inspired décor",
        "pots", "garden essentials", "photo frames", "candle holders",
        "desk organizers", "jute products", "bamboo solutions", "handcrafted home",
        "glassware"]),
    ("personal care", ["personal care", "self-care", "spa", "massages",
        "facials", "body scrubs", "sanitary", "skin, body, hair, and baby care"]),
    ("sustainable products", ["eco-friendly", "sustainable", "organic",
        "vegan", "cruelty free", "natural products"]),
    ("lifestyle accessories", ["smoking accessories", "rolling papers",
        "hookah products", "ashtrays", "lighters", "chillums", "charcoal"]),
    ("shoe care", ["sneaker care", "shoe care", "shoe cleaning"]),
    ("stationery", ["stamps online", "postage stamps", "stamp collection",
        "stamps of india"]),
    ("education & training", ["video lectures", "education revolution",
        "music education", "training institute", "online courses", "academy"]),
    ("printing & signage", ["signage", "sign board", "sticker printing",
        "poster maker", "acrylic board", "printing"]),
    ("general merchandise", ["multi category", "daily-use items",
        "everyday essentials", "unique products and categories", "indian goods"]),
]

def classify(desc):
    text = (desc or "").lower().replace("’", "'")
    for category, keywords in RULES:
        if any(k in text for k in keywords):
            return category
    return "unknown"

def load_audit():
    result = {}
    if not AUDIT_JSONL.exists():
        return result
    with AUDIT_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in ("final_url", "source_candidate"):
                value = str(item.get(key, "")).lower().rstrip("/")
                if value:
                    result[value] = item
    return result

def main():
    if not INPUT_CSV.exists():
        raise SystemExit(f"Missing: {INPUT_CSV}")

    with INPUT_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    audit = load_audit()
    category_changes = 0
    state_changes = 0

    for row in rows:
        if row.get("category", "").strip().lower() == "unknown":
            category = classify(row.get("tagline_description", ""))
            if category != "unknown":
                row["category"] = category
                category_changes += 1

        if not row.get("state", "").strip():
            key = row["domain_url"].lower().rstrip("/")
            item = audit.get(key)
            if item:
                evidence = item.get("india_evidence", [])
                state = next(
                    (x.split(":", 1)[1] for x in evidence if x.startswith("state:")),
                    None,
                )
                if not state:
                    city = next(
                        (x.split(":", 1)[1] for x in evidence if x.startswith("indian_city:")),
                        None,
                    )
                    state = CITY_STATE.get(city)

                if state:
                    row["state"] = state
                    state_changes += 1

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    unknown = sum(r["category"].strip().lower() == "unknown" for r in rows)
    missing_state = sum(not r["state"].strip() for r in rows)

    print(f"Category changes: {category_changes}")
    print(f"State changes: {state_changes}")
    print(f"Category unknown remaining: {unknown}")
    print(f"State missing remaining: {missing_state}")
    print(f"Output: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
