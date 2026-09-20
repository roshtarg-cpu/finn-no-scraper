# Finn.no Scraper

Scrapes listings from Finn.no, Norway's largest classifieds platform. This actor extracts comprehensive data from real estate, car, job, and other listings.

## Features

- 🏠 **Real Estate Listings** - Homes, apartments, cabins, commercial properties
- 🚗 **Car Listings** - Used and new vehicles with specifications
- 💼 **Job Listings** - Job postings with company and position details
- 📦 **Other Categories** - Electronics, furniture, services, and more
- 🖼️ **Image Extraction** - Captures listing images (up to 10 per listing)
- 📊 **Comprehensive Data** - Title, price, location, description, seller info, attributes
- 🔄 **Pagination Support** - Automatically follows next page links
- 🛡️ **Anti-Detection** - Uses Playwright with stealth techniques
- ⚡ **Efficient** - Rate-limited and respectful scraping

## Input Parameters

### Start URL (required)
The URL of the Finn.no search or category page to scrape.

**Examples:**
- Real estate: `https://www.finn.no/realestate/homes/search.html`
- Cars: `https://www.finn.no/car/used/search.html`
- Jobs: `https://www.finn.no/job/fulltime/search.html`
- Electronics: `https://www.finn.no/bap/forsale/search.html?category=0.93`

You can also use filtered search URLs with location, price range, etc.

### Maximum Pages (optional)
Maximum number of search result pages to scrape. Default: 10

Each page typically contains 20-50 listings depending on the category.

## Output Format

The actor outputs a dataset with the following fields:

```json
{
  "url": "https://www.finn.no/ad/...",
  "title": "Beautiful apartment in Oslo",
  "price": "5 000 000 kr",
  "priceNumeric": 5000000,
  "location": "Oslo, Grünerløkka",
  "description": "Spacious 3-bedroom apartment...",
  "category": "real_estate",
  "seller": "Real Estate Agency AS",
  "images": [
    "https://images.finn.no/...",
    "..."
  ],
  "imageCount": 8,
  "attributes": {
    "Property type": "Apartment",
    "Bedrooms": "3",
    "Square meters": "95",
    "Year built": "2015"
  },
  "scrapedAt": "2024-01-15T10:30:00.000Z"
}
```

### Field Descriptions

- **url** - Direct link to the listing page
- **title** - Listing title/headline
- **price** - Price as displayed (with currency and formatting)
- **priceNumeric** - Price as a number (for sorting/filtering)
- **location** - Address or location description
- **description** - Full listing description
- **category** - Detected category: `real_estate`, `car`, `job`, or `other`
- **seller** - Seller/advertiser name
- **images** - Array of image URLs
- **imageCount** - Number of images
- **attributes** - Category-specific attributes (varies by listing type)
- **scrapedAt** - ISO timestamp of when the data was scraped

## Usage Examples

### Scrape Real Estate Listings in Oslo

```json
{
  "startUrl": "https://www.finn.no/realestate/homes/search.html?location=0.20061",
  "maxPages": 5
}
```

### Scrape Used Cars

```json
{
  "startUrl": "https://www.finn.no/car/used/search.html",
  "maxPages": 10
}
```

### Scrape Job Listings

```json
{
  "startUrl": "https://www.finn.no/job/fulltime/search.html",
  "maxPages": 3
}
```

## Rate Limiting

The actor includes built-in rate limiting:
- 1 second delay between listings
- 2 seconds delay between pages

This ensures respectful scraping and reduces the chance of being blocked.

## robots.txt Compliance

The actor respects Finn.no's robots.txt file. Finn.no generally allows crawling of public listing pages but may have restrictions on certain areas.

## Data Quality

The scraper uses multiple fallback selectors to ensure robust data extraction even if Finn.no updates their HTML structure. If a field cannot be extracted, it will be omitted from the output rather than returning null values.

## Common Issues

### No listings found
- Verify the start URL is a valid Finn.no search/category page
- Some categories may use different URL structures
- Check if the page requires login or has regional restrictions

### Incomplete data
- Some listing types have different structures
- Private sellers may have less information than professional advertisers
- Very old listings may use different HTML templates

## Technical Details

- **Browser**: Playwright Chromium with anti-detection
- **Language**: Python 3.11
- **SDK**: Apify SDK 2.x
- **Concurrency**: Sequential processing to avoid overloading the site
- **Memory**: Recommended 2GB minimum
- **Timeout**: 30 seconds per page load

## Support

For issues, feature requests, or questions, please contact the actor developer.

## License

This actor is provided as-is for educational and commercial use. Please ensure you comply with Finn.no's Terms of Service and applicable data protection regulations (GDPR) when using this actor.
