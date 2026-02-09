import asyncio
import json
import hashlib
import logging
import re
from datetime import datetime, timezone
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import litellm

logger = logging.getLogger(__name__)

LLM_MODEL = "ollama/qwen3:8b"
OLLAMA_API_BASE = "http://localhost:11434"


class CrawlerAgent:
    """
    LLM-powered crawler agent using Crawl4AI.

    Strategy:
    1. Crawl4AI fetches search pages (with pagination)
    2. Extract listing URLs using BOTH regex + LLM (hybrid approach)
    3. For each listing: Crawl4AI fetches → returns markdown
    4. Raw HTML stored in MinIO (Bronze), markdown sent to Extractor
    """

    def __init__(self, model=LLM_MODEL, api_base=OLLAMA_API_BASE):
        self.model = model
        self.api_base = api_base
        logger.info(f"CrawlerAgent initialized | model={model}")

    async def _crawl_page(self, url: str) -> dict:
        """Fetch a page using Crawl4AI — returns markdown + raw HTML."""
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                logger.error(f"Crawl4AI failed for {url}: {result.error_message}")
                return {"markdown": "", "html": "", "links": [], "success": False}

            # Extract all links from the page
            internal_links = []
            if result.links:
                internal_links = [
                    link.get("href", "")
                    for link in result.links.get("internal", [])
                    if link.get("href")
                ]

            return {
                "markdown": result.markdown or "",
                "html": result.html or "",
                "links": internal_links,
                "success": True,
            }

    def _call_llm(self, prompt: str) -> str:
        """Call Qwen3 8B via LiteLLM."""
        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_base=self.api_base,
                temperature=0,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""

    def _parse_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        text = text.strip()
        if "<think>" in text:
            text = text.split("</think>")[-1].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        elif "{" in text:
            start = text.index("{")
            end = text.rindex("}") + 1
            text = text[start:end]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _extract_urls_regex(self, html: str, links: list, base_url: str) -> list:
        """
        Fast regex extraction of listing URLs — no LLM needed.
        Works for known Tunisian sites.
        """
        listing_urls = set()

        # Pattern for Tayara listing URLs
        tayara_pattern = re.compile(
            r'https?://(?:www\.)?tayara\.tn/item/[^"\s<>\']+',
            re.IGNORECASE
        )

        # Pattern for Mubawab listing URLs
        mubawab_pattern = re.compile(
            r'https?://(?:www\.)?mubawab\.tn/fr/[^"\s<>\']*\d+\.htm',
            re.IGNORECASE
        )

        # Pattern for Tunisie Annonce
        ta_pattern = re.compile(
            r'https?://(?:www\.)?tunisie-annonce\.com/AnnsDetail[^"\s<>\']+',
            re.IGNORECASE
        )

        # Search in HTML
        for pattern in [tayara_pattern, mubawab_pattern, ta_pattern]:
            listing_urls.update(pattern.findall(html))

        # Search in extracted links
        for link in links:
            if "/item/" in link and "tayara" in link:
                listing_urls.add(link)
            elif "mubawab" in link and ".htm" in link:
                listing_urls.add(link)
            elif "tunisie-annonce" in link and "AnnDetail" in link:
                listing_urls.add(link)

        # Ensure full URLs
        clean_urls = set()
        for url in listing_urls:
            if url.startswith("http"):
                clean_urls.add(url.split("?")[0])  # Remove query params
            elif url.startswith("/"):
                clean_urls.add(base_url + url)

        return list(clean_urls)

    def _generate_minio_key(self, url: str) -> str:
        """Generate MinIO object key: YYYY/MM/DD/{url_hash}.html"""
        now = datetime.now(timezone.utc)
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"{now.strftime('%Y/%m/%d')}/{url_hash}.html"

    def _get_pagination_urls(self, base_search_url: str, max_pages: int) -> list:
        """Generate paginated search URLs for known sites."""
        urls = []

        if "tayara.tn" in base_search_url:
            for page in range(1, max_pages + 1):
                sep = "&" if "?" in base_search_url else "?"
                urls.append(f"{base_search_url}{sep}page={page}")

        elif "mubawab.tn" in base_search_url:
            for page in range(1, max_pages + 1):
                urls.append(f"{base_search_url}:p:{page}")

        elif "tunisie-annonce" in base_search_url:
            for page in range(1, max_pages + 1):
                urls.append(f"{base_search_url}&page={page}")

        else:
            urls.append(base_search_url)

        return urls

    def discover_listings(self, search_url: str, max_pages: int = 5) -> list:
        """
        Discover listing URLs across multiple search result pages.
        Uses HYBRID approach: regex first (fast), LLM as fallback.
        """
        logger.info(f"=== Discovering listings | max_pages={max_pages} ===")

        all_urls = set()
        page_urls = self._get_pagination_urls(search_url, max_pages)
        base_url = "/".join(search_url.split("/")[:3])

        for i, page_url in enumerate(page_urls):
            logger.info(f"[Page {i + 1}/{len(page_urls)}] {page_url}")

            crawl_result = asyncio.run(self._crawl_page(page_url))

            if not crawl_result["success"]:
                logger.warning(f"  Failed to crawl page {i + 1}")
                continue

            # Method 1: Fast regex extraction from HTML + links
            regex_urls = self._extract_urls_regex(
                crawl_result["html"],
                crawl_result["links"],
                base_url,
            )
            logger.info(f"  Regex found: {len(regex_urls)} URLs")
            all_urls.update(regex_urls)

            # Method 2: LLM fallback (only if regex found nothing)
            if not regex_urls:
                logger.info("  Regex found nothing → asking LLM...")
                llm_urls = self._discover_with_llm(
                    crawl_result["markdown"], base_url
                )
                logger.info(f"  LLM found: {len(llm_urls)} URLs")
                all_urls.update(llm_urls)

            # Stop if no new URLs on this page (end of results)
            if not regex_urls:
                logger.info("  No more listings found, stopping pagination")
                break

        logger.info(f"=== Total unique URLs discovered: {len(all_urls)} ===")
        return list(all_urls)

    def _discover_with_llm(self, markdown: str, base_url: str) -> list:
        """Fallback: use LLM to find listing URLs when regex fails."""
        from agents.prompts.listing_extraction import DISCOVER_LINKS_PROMPT

        prompt = DISCOVER_LINKS_PROMPT.format(
            markdown=markdown[:6000],
            base_url=base_url,
        )
        llm_response = self._call_llm(prompt)
        result = self._parse_json(llm_response)
        return result.get("listing_urls", [])

    def crawl_listing(self, listing_url: str) -> dict:
        """Crawl a single listing page → markdown + raw HTML."""
        logger.info(f"Crawling: {listing_url}")

        crawl_result = asyncio.run(self._crawl_page(listing_url))

        if not crawl_result["success"]:
            return {"url": listing_url, "success": False, "error": "Crawl failed"}

        return {
            "url": listing_url,
            "success": True,
            "markdown": crawl_result["markdown"],
            "raw_html": crawl_result["html"],
            "raw_html_key": self._generate_minio_key(listing_url),
            "source": self._get_source_name(listing_url),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def run(self, search_url: str, max_pages: int = 100, max_listings: int = 1000) -> list:
        """
        Full crawler pipeline:
        1. Crawl search pages (with pagination) → discover URLs
        2. For each URL: Crawl4AI fetches → returns markdown + HTML
        """
        logger.info(f"=== Crawler Agent Starting ===")
        logger.info(f"  Search URL:   {search_url}")
        logger.info(f"  Max pages:    {max_pages}")
        logger.info(f"  Max listings: {max_listings}")

        # Step 1: Discover all listing URLs (paginated)
        listing_urls = self.discover_listings(search_url, max_pages=max_pages)

        if not listing_urls:
            logger.warning("No listing URLs discovered")
            return []

        logger.info(f"Will crawl {min(len(listing_urls), max_listings)} of {len(listing_urls)} URLs")

        # Step 2: Crawl each listing
        results = []
        for i, url in enumerate(listing_urls[:max_listings]):
            logger.info(f"[{i + 1}/{min(len(listing_urls), max_listings)}] {url}")
            result = self.crawl_listing(url)

            if result["success"]:
                results.append(result)
            else:
                logger.warning(f"  ❌ Failed: {result.get('error')}")

        logger.info(f"=== Crawler Done | {len(results)}/{len(listing_urls)} succeeded ===")
        return results

    def _get_source_name(self, url: str) -> str:
        domain = url.split("/")[2].lower()
        if "tayara" in domain:
            return "tayara"
        elif "mubawab" in domain:
            return "mubawab"
        elif "tunisie-annonce" in domain:
            return "tunisie_annonce"
        elif "affare" in domain:
            return "affare"
        return domain