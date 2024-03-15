from scrapy.spiders import SitemapSpider
from scrapy import signals
from scrapy.signalmanager import dispatcher
from livablproject.items import LivablprojectItem
import json
import re
from html import unescape

class LivablSitemapSpider(SitemapSpider):
    name = 'livabl_sitemap'
    allowed_domains = ['www.livabl.com']
    sitemap_urls = ['https://www.livabl.com/sitemaps/sitemap-developments-1.xml']
    sitemap_rules = [('(/[a-z\-]+-[a-z]{2}/[^/]+)$', 'parse_project')]

    def __init__(self, *args, **kwargs):
        super(LivablSitemapSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse_project(self, response):
        item = LivablprojectItem()
        selectors = {
            'name': 'div.name-container h1.name::text',
            'status': 'div.listing-status-wrapper div.current-listing-status span.listing-status-text::text',
            'price': 'div.price-wrapper span.sale-val::text',
            'incentives': 'div.price-incentive-container a::text',
            'address': 'div.address-wrapper-container span::text',
            'developer': 'a.developer-name::text',
            'buildingType': 'div.dev-summary .col-lg-4:nth-child(1) .content-text span::text',
            'unitsStories': 'div.dev-summary .col-lg-4:nth-child(2) .content-text span::text',
            'bedrooms': 'div.dev-summary .col-lg-4:nth-child(3) .content-text span::text',
            'sizeSqFt': 'div.dev-summary .col-lg-4:nth-child(5) .content-text span::text',
            'estimatedCompletion': 'div.dev-summary .col-lg-4:nth-child(4) .content-text span::text',
        }
        for field, css_selector in selectors.items():
            # Extract data using CSS selectors
            data = response.css(css_selector).get()
            # Clean data with strip() if it exists, otherwise set a placeholder
            item[field] = data.strip() if data else "Not available"
        # Extract data from hidden input field containing JSON
        units_json_str = response.css('input#hdDevelopmentUnits::attr(value)').get()
        # If JSON is present, decode it and assign to 'units' field, otherwise set a placeholder
        if units_json_str:
            units_json = json.loads(unescape(units_json_str))
            item['units'] = units_json
        else:
            item['units'] = "Not available"

        # Extract JSON data from the <script> tag as an example
        script_content = response.xpath("//script[contains(., 'GalleryID')]/text()").get()
        if script_content:
            item['galleryData'] = self.decode_json_from_script(script_content)
        else:
            item['galleryData'] = "Not available"
        yield item

    def decode_json_from_script(self, script):
        json_pattern = re.compile(r'\.html\((.*?)\)\.val\(\);', re.DOTALL)
        match = json_pattern.search(script)
        if match:
            json_str = unescape(match.group(1)[1:-1])  # Remove the leading and trailing JavaScript quotes and decode HTML entities
            try:
                json_data = json.loads(json_str)
                return json_data
            except json.JSONDecodeError as e:
                self.logger.error(f'Error decoding JSON: {e}')
        return "Not available"  # Return "Not available" if the regex didn't match or if parsing failed

    def spider_closed(self, spider):
        # Perform any cleanup here
        self.logger.info(f'Spider {spider.name} is closing.')