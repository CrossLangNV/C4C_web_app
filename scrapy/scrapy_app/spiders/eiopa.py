from datetime import datetime

import scrapy


class EiopaSpider(scrapy.Spider):
    download_delay = 10.0
    name = "eiopa"
    start_urls = [
        'https://www.eiopa.europa.eu/document-library_en?field_term_document_type_tid%5B0%5D=654&field_term_document_type_tid%5B1%5D=502',
    ]

    def parse(self, response):
        for div in response.css("div.view-content div.grid-list-item"):
            meta = {
                'title_prefix': div.css("div.title-prefix::text").extract_first(),
                'title': div.css("div.title::text").extract_first(),
                'date': div.css("span.date::text").extract_first(),
                'type': div.css("span.type::text").extract_first(),
                'doc_link': div.css("a::attr(href)").extract_first()
            }
            yield scrapy.Request(meta['doc_link'], callback=self.parse_single, meta=meta)

        next_page_url = response.css("li.next:not([class^='disabled']) > a::attr(href)").extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))

    def parse_single(self, response):
        data = {
            'title_prefix': response.meta['title_prefix'],
            'title': response.meta['title'],
            'date': datetime.strptime(response.meta['date'], '%d %b %Y'),
            'type': response.meta['type'],
            'url': response.url,
            'summary': response.css("div[id='main-content'] ::text").extract(),
            'pdf_docs': response.css("a.related-item.file-type-pdf::attr(href)").extract()
        }
        return data
