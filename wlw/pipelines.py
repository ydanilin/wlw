# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import re
from scrapy import logformatter
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class WlwPipeline(object):

    def process_item(self, item, spider):
        firmaId = item['firmaId']
        addrSplitted = re.split(r',\s+', item['full_addr'])
        if len(addrSplitted) == 2:
            stHaus, indStadt = addrSplitted
            indSplitted = re.split(r'(DE-\d+)\s?', indStadt)
            if len(indSplitted) == 3:
                dummy, index, stadt = indSplitted
                item['zip'] = index
                item['city'] = stadt
            else:
                logger.error(
                    'when re.split index, city for {0}'.format(firmaId))
            streetSplitted = stHaus.rsplit(' ', 1)
            if len(streetSplitted) == 2:
                street, house = streetSplitted
                item['street'] = street
                item['building'] = house
            else:
                logger.error('when re.split street, for {0}'.format(firmaId))
        else:
            logger.error('when re.split full address for {0}'.format(firmaId))
        phoneRe = re.search(r'<a [^>]+>([^<]+)<\/a>', item['phone'])
        if phoneRe.lastindex == 1:
            item['phone'] = phoneRe.group(1).strip()
        else:
            logger.error('when parsing phone tag for {0}'.format(firmaId))
        return item


class DuplicatesPipeline(object):

    def __init__(self, stats):
        self.ids_seen = set()
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.stats)
        return s

    def process_item(self, item, spider):
        if item['firmaId'] in self.ids_seen:
            self.stats.inc_value('Duplicated_firms')
            raise DropItem("Duplicate item found for: %s" % item['firmaId'])
        else:
            self.ids_seen.add(item['firmaId'])
            return item


class PoliteLogFormatter(logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            'level': logging.DEBUG,
            'msg': logformatter.DROPPEDMSG,
            'args': {
                'exception': exception,
                'item': item,
            }
        }
