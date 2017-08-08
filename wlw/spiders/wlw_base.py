# -*- coding: utf-8 -*-
import logging
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import HtmlResponse
from scrapy.shell import inspect_response
from ..items import WlwItem, WlwLoader
from ..dbms import DBMS

logger = logging.getLogger(__name__)


class WlwBaseSpider(CrawlSpider):
    def __init__(self, *args, **kwargs):
        super(WlwBaseSpider, self).__init__(*args, *kwargs)
        self.dbms = DBMS(self.name + '.db')

    name = 'wlw_base'
    allowed_domains = ['wlw.de']
    start_urls = ['Druckereien']#,
                  # 'Werbetechnik']

    def huj(value):
        # exclude
        t1 = value.find('/bogenoffsetdruck?')
        t2 = value.find('/druck-von-buechern?')
        t3 = value.find('/grossformatdruck?')
        t4 = value.find('/kataloge?')
        t5 = value.find('/offsetdruck?')
        t6 = value.find('/siebdruck?')
        t7 = value.find('/textildruck?')

        if t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0 or t5 >= 0 or t6 >= 0 or t7 >= 0:
            logger.info('Link dropped: {0}'.format(value))
            return None
        else:
            return value

    rules = (
        # 0. to go from start urls keyword synonym list to specific tifedruck
        Rule(LinkExtractor(restrict_css='a.list-group-item', process_value=huj)
             ),
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
            req.meta['job_dat'] = dict(initial_term=url, firms_pulled=0)
            yield req

    def parse_group(self, response):
        l = WlwLoader(item=WlwItem(), response=response)
        l.add_xpath('firmaId', '(.//*[@data-company-id]/@data-company-id)[1]')
        l.add_value(None, self.responseMetaDict(response))
        vcard = l.nested_css('div.profile-vcard')
        nameAddr = vcard.nested_css('div.vcard-details')
        nameAddr.add_xpath('name', 'h1//text()')
        nameAddr.add_xpath('full_addr', 'p//text()')
        svgSelector = vcard.nested_xpath('.//svg').selector
        vcard.add_value('site', svgSelector)
        vcard.add_value('email', svgSelector)
        vcard.add_value('phone', svgSelector)

        angebotSel = l.nested_xpath(
            '//div[@id="products-content"]//article').selector
        vcard.add_value('angebots', angebotSel)

        facts = l.nested_xpath('.//div[@id="data-and-facts-content"]/article')
        l.add_value('delivery', facts.selector)
        l.add_value('facts', facts.selector)
        l.add_value('certificates', facts.selector)

        container = l.load_item()

        # inspect_response(response, self)
        return container

    def responseMetaDict(self, response):
        return dict(query=response.meta['job_dat']['initial_term'],
                    category=response.meta['job_dat']['category'],
                    total_firms=response.meta['job_dat']['total'])

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            linksGot = len(links)
            response.meta['job_dat']['linksGot'] = linksGot
            for link in links:
                seen.add(link)
                r = self._build_request(n, link)
                yield rule.process_request(r)