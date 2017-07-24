# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.shell import inspect_response


class WlwBaseSpider(CrawlSpider):
    name = 'wlw_base'
    allowed_domains = ['wlw.de']
    start_urls = ['Druckereien']#,
                  # 'Werbetechnik']

    def huj(value):
        t1 = value.find('blaudruck')
        t2 = value.find('golddruck')
        t3 = value.find('kranzschleifendruck')
        t4 = value.find('lithographie-steindruck')
        t5 = value.find('tiefdruck')
        if t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0 or t5 >= 0:
            return value
        else:
            return None

    rules = (
        # 0. to go from start urls keyword synonym list to specific tifedruck
        Rule(LinkExtractor(restrict_css='a.list-group-item', process_value=huj)),
        # 1. from firms list to specific firm
        Rule(LinkExtractor(
            restrict_xpaths='//a[@data-track-type="click_serp_company_name"]'),
            callback='parse_group'),
        # 2. from a firm list page to the next one
        Rule(LinkExtractor(restrict_xpaths=('//ul[@class="pagination"]/'
                                            'li[not(@class)]/'
                                            'a[text()[contains(.,"chste")]]')))
    )

    def start_requests(self):
        for url in self.start_urls:
            fullUrl = ('https://www.wlw.de/de/kategorien?utf8=%E2%9C%93'
                       '&entered_search=1&q=') + url
            req = self.make_requests_from_url(fullUrl)
            req.meta['process_data'] = dict(initial_term=url,
                                            firms_pulled=0)
            yield req



    def parse_group(self, response):
        # print('RESPONS: ', response.url)
        # print(response.meta['process_data'], '\n')
        ruleNo = response.meta.get('rule', 77)
        if ruleNo == 2:
            print('******************   Next page loaded')
        puk=1
        # inspect_response(response, self)

