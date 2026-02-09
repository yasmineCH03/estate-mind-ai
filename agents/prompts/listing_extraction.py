LISTING_EXTRACTION_PROMPT = """You are a real estate data extraction expert specialized in Tunisian property listings.

Given the following markdown text from a real estate listing page (crawled by Crawl4AI), extract ALL structured information.

RULES:
- Extract ONLY information explicitly mentioned in the text
- If a field is not mentioned, return null
- Price should be a number (no currency symbol, no dots for thousands)
- Governorate must be a valid Tunisian governorate
- Property type must be one of: apartment, house, villa, studio, land, commercial
- Transaction type must be: rent or sale
- "S+1" = 1 room, "S+2" = 2 rooms, "S+3" = 3 rooms, etc.
- Standing: low, medium, high, luxury
- Features: parking, elevator, garden, pool, furnished, balcony, terrace, security, air_conditioning, central_heating, sea_view

LISTING MARKDOWN:
---
{markdown}
---

Return ONLY a valid JSON object:
{{
    "title": "...",
    "property_type": "...",
    "transaction_type": "...",
    "price": number or null,
    "currency": "TND",
    "rooms": number or null,
    "bedrooms": number or null,
    "bathrooms": number or null,
    "area_m2": number or null,
    "floor": number or null,
    "address": "...",
    "city": "...",
    "delegation": "...",
    "governorate": "...",
    "features": ["...", "..."],
    "description": "cleaned summary",
    "standing": "...",
    "equipment": ["...", "..."]
}}

JSON:"""


DISCOVER_LINKS_PROMPT = """You are a web scraping assistant for Tunisian real estate websites.

I will give you markdown content from a real estate search results page (converted by Crawl4AI).
Find ALL links that point to individual property listing pages.

RULES:
- Only extract links to individual property/listing detail pages
- Ignore navigation, pagination, category, footer, social media links
- Return complete URLs
- Base domain: {base_url}

MARKDOWN CONTENT:
---
{markdown}
---

Return a JSON object:
{{"listing_urls": ["url1", "url2", ...]}}

JSON:"""