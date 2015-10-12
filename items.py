# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')  
from scrapy.item import Item, Field

class ShopItem(Item):
	name = Field()
	link = Field()
	lng = Field()
	lat = Field()
	
class DishItem(Item):
	name = Field()
	link = Field()
