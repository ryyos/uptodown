# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json

from itemadapter import ItemAdapter

from .items import UptodownItem
from .items import DetailItem

from icecream import ic
from .utils import *

class UptodownPipeline:

    def __init__(self) -> None:
        self.MAIN_PATH = 'data'
        ...

    def process_item(self, item, spider):
        
        if isinstance(item, UptodownItem):
            ic('UptodownItem')
            path = f'{create_dir(self.MAIN_PATH, item)}/{vname(item["detail_reviews"]["username_reviews"])}.json'

            results = dict(item)
            results.update({
                "path_data_raw": path,
                "path_data_clean": convert_path(path)
            })

            with open(path, 'w', encoding= "utf-8") as file:
                json.dump(results, file, ensure_ascii=False, indent=2, default=str)

        else:
            ic('DetailPipeline')
            path = f'{create_dir(self.MAIN_PATH, item)}/detail/{vname(item["detail_application"]["title"].lower())}.json'

            results = dict(item)
            results.update({
                "path_data_raw": path,
                "path_data_clean": convert_path(path)
            })

            with open(path, 'w', encoding= "utf-8") as file:
                json.dump(results, file, ensure_ascii=False, indent=2, default=str)
        