"""
Finn.no scraper - Extracts listings from Norway's largest classifieds platform.
Supports real estate, cars, jobs, and other categories.
"""
import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any

from apify import Actor
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class FinnNoScraper:
    """Scraper for finn.no listings."""
    
    def __init__(self, start_url: str, max_pages: int = 10):
        self.start_url = start_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def initialize_browser(self):
        """Initialize Playwright browser with anti-detection measures."""
        Actor.log.info("Initializing Playwright browser...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with anti-detection options
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='nb-NO',
            timezone_id='Europe/Oslo',
            extra_http_headers={
                'Accept-Language': 'nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en;q=0.6',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
        )
        
        # Apply stealth techniques
        await self.context.add_init_script("""
            // Overwrite the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite the plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Overwrite the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['nb-NO', 'nb', 'no', 'nn', 'en']
            });
            
            // Remove automation indicators
            window.chrome = {
                runtime: {}
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        Actor.log.info("Browser initialized successfully")
        
    async def close_browser(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def extract_listing_data(self, page: Page, listing_url: str) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing page."""
        try:
            Actor.log.info(f"Extracting data from: {listing_url}")
            
            await page.goto(listing_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)  # Small delay for dynamic content
            
            # Extract listing data
            data = {
                'url': listing_url,
                'scrapedAt': page.evaluate('new Date().toISOString()')
            }
            
            # Title
            title_selectors = [
                'h1[data-testid="object-title"]',
                'h1.u-t1',
                'h1',
                '[class*="heading"]'
            ]
            for selector in title_selectors:
                title = await page.query_selector(selector)
                if title:
                    data['title'] = (await title.text_content()).strip()
                    break
            
            # Price
            price_selectors = [
                '[data-testid="pricing-total"]',
                '[class*="price"]',
                '[class*="u-t2"]'
            ]
            for selector in price_selectors:
                price_elem = await page.query_selector(selector)
                if price_elem:
                    price_text = (await price_elem.text_content()).strip()
                    data['price'] = price_text
                    # Extract numeric price
                    price_match = re.search(r'([\d\s]+)', price_text.replace('\xa0', ' '))
                    if price_match:
                        data['priceNumeric'] = int(price_match.group(1).replace(' ', ''))
                    break
            
            # Location
            location_selectors = [
                '[data-testid="object-address"]',
                '[class*="location"]',
                'span[class*="address"]'
            ]
            for selector in location_selectors:
                location_elem = await page.query_selector(selector)
                if location_elem:
                    data['location'] = (await location_elem.text_content()).strip()
                    break
            
            # Description
            description_selectors = [
                '[data-testid="description"]',
                '[class*="description"]',
                'div[class*="u-word-break"]'
            ]
            for selector in description_selectors:
                desc_elem = await page.query_selector(selector)
                if desc_elem:
                    data['description'] = (await desc_elem.text_content()).strip()
                    break
            
            # Images
            image_selectors = [
                'img[data-testid="object-image"]',
                'img[class*="gallery"]',
                'picture img'
            ]
            images = []
            for selector in image_selectors:
                img_elements = await page.query_selector_all(selector)
                if img_elements:
                    for img in img_elements[:10]:  # Limit to 10 images
                        src = await img.get_attribute('src')
                        if src and not src.startswith('data:'):
                            images.append(src)
                    if images:
                        break
            
            if images:
                data['images'] = images
                data['imageCount'] = len(images)
            
            # Seller information
            seller_selectors = [
                '[data-testid="seller-name"]',
                '[class*="seller"]',
                'a[class*="contact"]'
            ]
            for selector in seller_selectors:
                seller_elem = await page.query_selector(selector)
                if seller_elem:
                    data['seller'] = (await seller_elem.text_content()).strip()
                    break
            
            # Key facts/attributes (varies by category)
            key_facts = {}
            facts_container = await page.query_selector('[data-testid="key-facts"]')
            if not facts_container:
                facts_container = await page.query_selector('[class*="key-info"]')
            
            if facts_container:
                fact_items = await facts_container.query_selector_all('dl dt, dl dd')
                key = None
                for item in fact_items:
                    tag_name = await item.evaluate('el => el.tagName.toLowerCase()')
                    text = (await item.text_content()).strip()
                    
                    if tag_name == 'dt':
                        key = text
                    elif tag_name == 'dd' and key:
                        key_facts[key] = text
                        key = None
            
            if key_facts:
                data['attributes'] = key_facts
            
            # Category detection
            parsed_url = urlparse(listing_url)
            path_parts = parsed_url.path.split('/')
            if 'realestate' in path_parts or 'eiendom' in listing_url:
                data['category'] = 'real_estate'
            elif 'car' in path_parts or 'bil' in listing_url:
                data['category'] = 'car'
            elif 'job' in path_parts or 'jobb' in listing_url:
                data['category'] = 'job'
            else:
                data['category'] = 'other'
            
            Actor.log.info(f"Successfully extracted data for: {data.get('title', 'Unknown')}")
            return data
            
        except Exception as e:
            Actor.log.error(f"Error extracting data from {listing_url}: {str(e)}")
            return None
    
    async def get_listing_urls(self, page: Page, list_page_url: str) -> List[str]:
        """Extract listing URLs from a list/search page."""
        try:
            Actor.log.info(f"Extracting listing URLs from: {list_page_url}")
            
            await page.goto(list_page_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)  # Wait for dynamic content
            
            # Find listing links
            listing_urls = []
            
            # Try multiple selectors for listing links
            link_selectors = [
                'article a[href*="/ad/"]',
                'a[href*="/ad/"]',
                '[class*="result"] a',
                '[data-testid="result-item"] a'
            ]
            
            for selector in link_selectors:
                links = await page.query_selector_all(selector)
                if links:
                    Actor.log.info(f"Found {len(links)} links with selector: {selector}")
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and '/ad/' in href:
                            full_url = urljoin('https://www.finn.no', href)
                            if full_url not in self.visited_urls:
                                listing_urls.append(full_url)
                                self.visited_urls.add(full_url)
                    
                    if listing_urls:
                        break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in listing_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            Actor.log.info(f"Extracted {len(unique_urls)} unique listing URLs")
            return unique_urls
            
        except Exception as e:
            Actor.log.error(f"Error getting listing URLs from {list_page_url}: {str(e)}")
            return []
    
    async def get_next_page_url(self, page: Page) -> Optional[str]:
        """Find the next page URL."""
        try:
            # Try different next page selectors
            next_selectors = [
                'a[rel="next"]',
                'a[aria-label*="Neste"]',
                'a[title*="Neste"]',
                'button[aria-label*="Neste"]'
            ]
            
            for selector in next_selectors:
                next_button = await page.query_selector(selector)
                if next_button:
                    href = await next_button.get_attribute('href')
                    if href:
                        next_url = urljoin(page.url, href)
                        Actor.log.info(f"Found next page: {next_url}")
                        return next_url
            
            return None
            
        except Exception as e:
            Actor.log.error(f"Error finding next page: {str(e)}")
            return None
    
    async def scrape(self):
        """Main scraping logic."""
        Actor.log.info(f"Starting scraper for {self.start_url}")
        Actor.log.info(f"Max pages to scrape: {self.max_pages}")
        
        await self.initialize_browser()
        
        try:
            page = await self.context.new_page()
            current_url = self.start_url
            pages_scraped = 0
            total_listings = 0
            
            while current_url and pages_scraped < self.max_pages:
                pages_scraped += 1
                Actor.log.info(f"Processing page {pages_scraped}/{self.max_pages}")
                
                # Get listing URLs from current page
                listing_urls = await self.get_listing_urls(page, current_url)
                
                if not listing_urls:
                    Actor.log.warning("No listing URLs found on page")
                    break
                
                # Process each listing
                for idx, listing_url in enumerate(listing_urls, 1):
                    Actor.log.info(f"Processing listing {idx}/{len(listing_urls)}")
                    
                    # Create new page for each listing
                    listing_page = await self.context.new_page()
                    
                    try:
                        listing_data = await self.extract_listing_data(listing_page, listing_url)
                        
                        if listing_data:
                            await Actor.push_data(listing_data)
                            total_listings += 1
                            Actor.log.info(f"Saved listing #{total_listings}: {listing_data.get('title', 'Unknown')}")
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    finally:
                        await listing_page.close()
                
                # Find next page
                current_url = await self.get_next_page_url(page)
                
                if not current_url:
                    Actor.log.info("No more pages to scrape")
                    break
                
                # Delay between pages
                await asyncio.sleep(2)
            
            Actor.log.info(f"Scraping completed. Total listings extracted: {total_listings}")
            
        finally:
            await self.close_browser()


async def main():
    """Main entry point for the Apify Actor."""
    async with Actor:
        Actor.log.info("Finn.no scraper starting...")
        
        # Get input
        actor_input = await Actor.get_input() or {}
        start_url = actor_input.get('startUrl', 'https://www.finn.no/realestate/homes/search.html')
        max_pages = actor_input.get('maxPages', 10)
        
        # Validate input
        if not start_url:
            Actor.log.error("startUrl is required")
            return
        
        if not start_url.startswith('http'):
            start_url = f"https://www.finn.no{start_url}"
        
        Actor.log.info(f"Input parameters: startUrl={start_url}, maxPages={max_pages}")
        
        # Create and run scraper
        scraper = FinnNoScraper(start_url=start_url, max_pages=max_pages)
        
        try:
            await scraper.scrape()
            Actor.log.info("Actor finished successfully")
        except Exception as e:
            Actor.log.error(f"Actor failed with error: {str(e)}")
            raise


if __name__ == '__main__':
    asyncio.run(main())
