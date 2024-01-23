# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json

from itemadapter import ItemAdapter
from icecream import ic
from .utils import create_dir

class UptodownPipeline:

    def __init__(self) -> None:
        self.MAIN_PATH = 'private'
        ...

    def process_item(self, item, spider):

        path = create_dir(item)
        ic(path)
        with open(path, 'w', encoding= "utf-8") as file:
            json.dump(item, file, ensure_ascii=False, indent=2, default=str)
        
