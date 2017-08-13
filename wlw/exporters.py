# -*- coding: utf-8 -*-

from scrapy.conf import settings
from scrapy.exporters import CsvItemExporter

class CSVcustomerItemExporter(CsvItemExporter):

    def __init__(self, *args, **kwargs):
        kwargs['fields_to_export'] = settings.getlist('EXPORT_FIELDS') or None

        super(CSVcustomerItemExporter, self).__init__(*args, **kwargs)