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
        if response.meta.get('rule', 77) == 2:
            logger.info('******************   Next page loaded')
        if response.meta.get('rule', 77) == 1:
            # means one firm already processed:
            x = self.stats.get_value('all_firms') - 1  # tuda
            self.stats.set_value('all_firms', x)  # tuda
            term = response.meta['process_data']['initial_term'] + '/' +\
                   response.meta['process_data']['classified_term']
            total = response.meta['process_data']['firms_total']
            t = self.stats.get_value(term)
            if not t:  # if synonym is not in the stats
                # create entry and set downloaded to 1
                self.stats.set_value(term, dict(downl=1,
                                                total=int(total)))
            else:
                t['downl'] += 1
                # signal when all firms for sysnonym are fetched
                if t['downl'] == response.meta['process_data']['firms_total']:
                    msg = ('For category %(c)s'
                           ' all firms fetched (%(a)d).'
                           ' %(x)d firms remain to process so far')
                    log_args = {'c': response.meta['process_data']['classified_term'],
                                'a': response.meta['process_data']['firms_total'],
                                'x': self.stats.get_value('all_firms')}
                    logger.info(msg, log_args)
        return None

    def process_spider_output(self, response, result, spider):
        allFirms = self.stats.get_value('all_firms')
        if not allFirms:  # that means we just started the process
            self.stats.set_value('all_firms', 0)
            allFirms = 0
        for i in result:
            if isinstance(i, Request):
                i.meta['process_data'] = response.meta['process_data'].copy()
                ruleNo = response.meta.get('rule', 77)
                # if response came from request triggered by
                # either rule 0: from synonyms page to firms listing first page
                # or rule 2: to next listing page
                if ruleNo in [0, 2]:
                    # synonym term and amount of firms
                    txt = re.split(r'(\d+) Anbieter',
                                   response.meta.get('link_text', ''))
                    if len(txt) == 3:
                        i.meta['process_data']['classified_term'] = txt[0]
                        i.meta['process_data']['firms_total'] = int(txt[1])
                        # one response synonyms page creates multiple requests
                        # to firms. so firms accumulator for same response
                        # should be here
                        # if we're first time on this response
                        if response.meta['process_data']['firms_pulled'] == 0:
                            # add firms from this synonym to total
                            was = allFirms
                            allFirms += int(txt[1])
                            self.stats.set_value('all_firms', allFirms)
                            msg = ('Added to queue: was %(w)d, added %(a)d')
                            args = {'w': was, 'a': int(txt[1])}
                            logger.info(msg, args)
                    # ... and request triggered by Rule 1 (to fetch firm page)
                    if i.meta.get('rule', 77) == 1:

                        # add to firms accumulator
                        count = response.meta['process_data']['firms_pulled']
                        count += 1
                        response.meta['process_data']['firms_pulled'] = count
                        # ... and copy this to request
                        i.meta['process_data']['firms_pulled'] = count
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
