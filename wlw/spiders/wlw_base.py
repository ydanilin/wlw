# -*- coding: utf-8 -*-
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.shell import inspect_response

logger = logging.getLogger(__name__)


class WlwBaseSpider(CrawlSpider):
    name = 'wlw_base'
    allowed_domains = ['wlw.de']
    start_urls = ['Druckereien']#,
                  # 'Werbetechnik']

    def huj(value):
        t1 = -2  # value.find('blaudruck')
        t2 = -2  # value.find('golddruck')
        t3 = -2  # value.find('kranzschleifendruck')
        t4 = -2  # value.find('lithographie-steindruck')
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
        firmaId = response.xpath(
            '(.//*[@data-company-id]/@data-company-id)[1]').extract_first().strip()

        vcardDiv = response.css('div.profile-vcard')
        if vcardDiv:
            nameAddrDiv = vcardDiv.css('div.vcard-details')
            if nameAddrDiv:
                t = self.parseNameAddress(nameAddrDiv, firmaId)
                # HFS Verpackungen GmbH
            else:
                logger.error('no name/address data for {0}'.format(firmaId))
            # go for phone, email, site
            t1 = self.parsePhoneEmail(vcardDiv)
            print(t1['email'], t1['site'], firmaId)
        else:
            logger.error('no visitcard section for {0}'.format(firmaId))

        angebotDiv = response.xpath('//div[@id="products-content"]')
        if angebotDiv:
            angebots = angebotDiv.xpath('.//article')
            for angebot in angebots:
                pass
                # print('Angebot explore')
        else:
            logger.error('no angebot section for {0}'.format(firmaId))
        # inspect_response(response, self)

    def parseNameAddress(self, nameAddrDiv, firmaId):
        output = {}
        nameAddrLst = nameAddrDiv.xpath('.//text()').extract()
        if len(nameAddrLst) == 2:
            output['name'] = nameAddrLst[0].strip()
            addrFull = nameAddrLst[1].strip()
            output['addrFull'] = addrFull
            addrSplitted = re.split(r',\s+', addrFull)
            if len(addrSplitted) == 2:
                stHaus, indStadt = addrSplitted
                indSplitted = re.split(r'(DE-\d+)\s?', indStadt)
                if len(indSplitted) == 3:
                    dummy, index, stadt = indSplitted
                    output['zip'] = index
                    output['city'] = stadt
                else:
                    logger.error('when re.split index, city for {0}'.format(firmaId))
                streetSplitted = re.split(r'\s+(\d+)', stHaus)
                if len(streetSplitted) == 3:
                    street, house, dummy = streetSplitted
                    output['street'] = street
                    output['building'] = house
                else:
                    logger.error('when re.split street, No for {0}'.format(firmaId))
            else:
                logger.error('when re.split full address for {0}'.format(firmaId))
        else:
            logger.error('parsing nameAddrDiv for {0}'.format(firmaId))
        return output

    def parsePhoneEmail(self, vcardDiv):
        phone = ''
        email = ''
        site = ''
        svgs = vcardDiv.xpath('.//svg')
        for svg in svgs:
            t = svg.extract()
            if t.find('"#svg-icon-earphone"') >= 0:
                aTag = svg.xpath('./ancestor::a[1]')
            elif t.find('"#svg-icon-email"') >= 0:
                email = svg.xpath('./ancestor::a[1]//text()').extract_first().strip()[::-1]
            elif t.find('"#svg-icon-website"') >= 0:
                site = svg.xpath('./ancestor::a[1]/@href').extract_first().strip()
        return dict(phone=phone, email=email, site=site)
