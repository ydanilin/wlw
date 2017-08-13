# -*- coding: utf-8 -*-
import logging
import re
from scrapy import signals
from scrapy.http import Request


logger = logging.getLogger(__name__)

class WlwSpiderMiddleware(object):
    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.stats)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # if response.meta.get('rule', 77) == 2:
        #     logger.info('******************   Next page loaded')
        rule = response.meta.get('rule')
        dat = response.meta['job_dat']
        if response.meta.get('rule', 77) == 1:
            # means one firm already processed:
            self.logPacket(response, spider)
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            if isinstance(i, Request):
                i.meta['job_dat'] = response.meta['job_dat'].copy()

                spawnedByRule = response.meta.get('rule')
                willRequestByRule = i.meta.get('rule')

                self.assignPage(spawnedByRule, willRequestByRule, response, i)

                if (not spawnedByRule) and (willRequestByRule == 0):
                    part = i.url.rsplit('?', 1)[0]
                    nameInUrl = part.rsplit('/', 1)[1]
                    catRecord = spider.dbms.getCategory(nameInUrl)
                    if catRecord:
                        # set discard flag here
                        category = catRecord['caption']
                        total = catRecord['total']
                        scraped = catRecord['scraped']
                        pages = spider.dbms.getPageSeen(nameInUrl)
                    else:  # open new category in db
                        txt = i.meta.get('link_text', '')
                        catDetails = re.split(r'(\d+) Anbieter', txt)
                        if len(catDetails) == 3:
                            category, total, dummy = catDetails
                            scraped = 0
                            pages = []
                            spider.dbms.addCategory(nameInUrl, category,
                                                    int(total))
                        else:
                            category = None
                            total = None
                            i.meta['job_dat']['discard'] = True
                            msg = ('cannot parse name & amounts for'
                                   ' category: {0}. Category discarded')
                            logger.error(msg.format(txt))
                    if scraped >= total:
                        i.meta['job_dat']['discard'] = True
                    else:
                        dic = dict(scraped=scraped, total=total, pages={},
                                   caption=category)
                        self.stats.set_value(nameInUrl, dic)
                    i.meta['job_dat']['nameInUrl'] = nameInUrl
                    i.meta['job_dat']['category'] = category
                    i.meta['job_dat']['total'] = int(total)

                if (spawnedByRule in [0, 2]) and (willRequestByRule == 1):
                    pageSeen = spider.dbms.getPageSeen(
                        i.meta['job_dat']['nameInUrl'])
                    if i.meta['job_dat']['page'] in pageSeen:
                        i.meta['job_dat']['discard'] = True
                    fid = int(i.meta['firmaId'])
                    if fid in spider.ids_seen:
                        i.meta['job_dat']['discard'] = True
                        self.logPacket(i, spider, supress_scraped=True)
                        logger.warning(
                            "Duplicate request found for: %s" % i.meta['firmaId'])
                        self.stats.inc_value('Duplicated_requests')

                # final decision
                a = i.meta.get('job_dat', {})
                discard = i.meta.get('job_dat', {}).get('discard')
                if not discard:
                    yield i
            else:
                yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    def assignPage(self, spawnedByRule, willRequestByRule, resp, req):
        if (not spawnedByRule) and (willRequestByRule == 0):
            req.meta['job_dat']['page'] = 1
        if spawnedByRule in [0, 2]:
            if willRequestByRule == 1:
                pg = resp.meta['job_dat']['page']
                req.meta['job_dat']['page'] = pg
            if willRequestByRule == 2:
                pg = resp.meta['job_dat']['page']
                req.meta['job_dat']['page'] = pg + 1

    def logPacket(self, packet, spider, supress_scraped=False):
        nameInUrl = packet.meta['job_dat']['nameInUrl']
        page = packet.meta['job_dat']['page']
        record = self.stats.get_value(nameInUrl)
        pg = record['pages'].get(page, 0) + 1
        record['pages'][page] = pg
        if not supress_scraped:
            scr = record['scraped'] + 1
        else:
            scr = record['scraped']
        record['scraped'] = scr
        self.stats.set_value(nameInUrl, record)

        if not supress_scraped:
            spider.dbms.updateScraped(nameInUrl, scr)

            if pg == packet.meta['job_dat']['linksGot']:
                spider.dbms.addPageSeen(nameInUrl, page)

            if scr == packet.meta['job_dat']['total']:
                # signal when all firms for sysnonym are fetched
                msg = ('For category %(c)s'
                       ' all firms fetched (%(a)d).')
                query = packet.meta['job_dat']['initial_term']
                classif = packet.meta['job_dat']['category']
                log_args = {'c': query + '/' + classif,
                            'a': packet.meta['job_dat']['total']}
                logger.info(msg, log_args)
