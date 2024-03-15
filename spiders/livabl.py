import scrapy
import json
import re
import csv
from html import unescape
from livablproject.items import LivablprojectItem

class LivablSpider(scrapy.Spider):
    name = 'livabl'
    allowed_domains = ['www.livabl.com']
    start_urls = ['https://www.livabl.com/sitemaps/sitemap-developments-1.xml']

    def parse(self, response):
        # Use a regex pattern to match URLs that include the city and province format:
        # https://www.livabl.com/{city}-{province-code}/{project-name} without trailing segments.
        url_pattern = re.compile(r'https://www.livabl.com/[a-z\-]+-[a-z]{2}/[a-z0-9\-]+$')

        # Find URLs in the sitemap XML and apply the regex pattern
        sitemap_links = response.xpath('//url/loc/text()').getall()
        for url in sitemap_links:
            if url_pattern.match(url):
                # Only yield a request if the URL matches the pattern
                yield scrapy.Request(url=url, callback=self.parse_project)
            else:
                self.logger.info(f'Skipping URL: {url}')

    def decode_json_from_script(self, script):
        json_pattern = re.compile(r'\.html\((.*?)\)\.val\(\);', re.DOTALL)
        match = json_pattern.search(script)

        if match:
            json_str = unescape(match.group(1)[1:-1])  # Decode HTML entities and strip quotes
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON: {e}")
        return None

# items.py
# Make sure this file has the correct LivablprojectItem definition.

    def parse(self, response):
        item = LivablprojectItem()
        item['name'] = response.css('div.name-container h1.name::text').get(default='')
        item['status'] = response.css('div.listing-status-wrapper div.current-listing-status span.listing-status-text::text').get().strip()
        item['price'] = response.css('div.price-wrapper span.sale-val::text').get().strip()
        item['incentives'] = response.css('div.price-incentive-container a::text').get().strip()
        item['address'] = ''.join(response.css('div.address-wrapper-container span::text').getall()).strip()
        item['developer'] = response.css('a.developer-name::text').get().strip()
       
        # Correctly extracting building type, units, and bedrooms
        item['buildingType'] = response.css('div.dev-summary .col-lg-4:nth-child(1) .content-text span::text').get().strip()
        item['unitsStories'] = response.css('div.dev-summary .col-lg-4:nth-child(2) .content-text span::text').get().strip()
        item['bedrooms'] = response.css('div.dev-summary .col-lg-4:nth-child(3) .content-text span::text').get().strip()  # Adjusted for correct field

        # Adjusting the extraction for sizeSqFt and estimatedCompletion
        item['sizeSqFt'] = response.css('div.dev-summary .col-lg-4:nth-child(5) .content-text span::text').get().strip()  # Correct field for SqFt
        item['estimatedCompletion'] = response.css('div.dev-summary .col-lg-4:nth-child(4) .content-text span::text').get().strip()  # New field for completion date

        # Extract and process data from the hidden input field
        raw_json_str = response.css('input#hdDevelopmentUnits::attr(value)').get()
        if raw_json_str:
            decoded_json_str = unescape(raw_json_str)
            units_data = json.loads(decoded_json_str)
            item['units'] = units_data
        # Extract and process data from <script> tag
        script_content = response.xpath("//script[contains(., 'GalleryID')]/text()").get()
        if script_content:
            gallery_data = self.decode_json_from_script(script_content)
            if gallery_data:
                item['galleryData'] = gallery_data
        yield item

# items.py
# class LivablprojectItem(scrapy.Item):
#     name = scrapy.Field()
#     units = scrapy.Field()
#     galleryData = scrapy.Field()
#     # Other fields...