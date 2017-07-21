# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.shell import inspect_response


class WlwBaseSpider(CrawlSpider):
    name = 'wlw_base'
    allowed_domains = ['wlw.de']
    start_urls = ['https://www.wlw.de/de/kategorien?utf8=%E2%9C%93&entered_search=1&q=Druckereien',
                  'https://www.wlw.de/de/kategorien?utf8=%E2%9C%93&entered_search=1&q=Werbetechnik']
    rules = (
        Rule(LinkExtractor(restrict_css='a.list-group-item'), callback='parse_group'),
    )

    def parse_group(self, response):
        print('RESPONS: ', response.url)
        inspect_response(response, self)
        pass

