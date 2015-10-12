#coding:utf-8

import os
import sys  
import time
import re
import urllib
import scrapy
from scrapy.contrib.spiders import CrawlSpider
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from dishRec.items import ShopItem, DishItem 

# set default encoding
reload(sys)  
sys.setdefaultencoding('gbk')  

class DishRecSpider(CrawlSpider):
	MAX_PAGE_IDX = 10
	IMG_ROOT_DIR = 'E:\\ICME_dishRec\\image'
	SMALL_IMG_SIZE_STR = '240c180'
	LARGE_IMG_SIZE_STR = '700x700'
	DISH_LOG_DIR = '../dish.txt'
	
	name = 'dishRecSpider'
	allowed_domains = ['dianping.com']
	rootUrl = 'http://www.dianping.com'
	download_delay = 1.5
	pageIdx = 1
	
	start_urls = ['http://www.dianping.com/search/category/2/10/r6979d1o10']
				
	def parse(self, response):
		# print '\n' + response.url + '\n'
		
		hxs = HtmlXPathSelector(response)
		shopInfoList = hxs.select('//a[@data-hippo-type="shop"]')

		for shopInfo in shopInfoList:
			shopUrl = self.rootUrl + shopInfo.select('@href').extract()[0]
			yield Request(url = shopUrl, callback = self.parse_dish)
		
		if self.pageIdx < self.MAX_PAGE_IDX:
			self.pageIdx = self.pageIdx + 1
			yield Request(url = self.start_urls[0] + 'p%d' %self.pageIdx, callback = self.parse)
		
	def parse_dish(self, response): 
	
		#------parse the name and coordinate of the restaurant
		
		hxs = HtmlXPathSelector(response)
		shopName = hxs.select('//h1[@class="shop-name"]/text()').extract()[0]
		
		coordScript = hxs.select('//div[@id="aside"]/script[1]').extract()[0]
		coordTupleText = re.findall(r'lng:\w+.\w+,lat:\w+.\w+', coordScript)[0]
		
		lngPre = re.search(r'lng:', coordTupleText)
		latPre = re.search(r'lat:', coordTupleText)
		
		sItem = ShopItem()
		sItem['name'] = shopName.strip()
		sItem['link'] = response.url
		sItem['lng'] = coordTupleText[lngPre.end() : latPre.start()-1]
		sItem['lat'] = coordTupleText[latPre.end() : len(coordTupleText)]
		
		#fid = open(self.DISH_LOG_DIR,'a')
		#fid.write(sItem['name'] + '\n' + sItem['link'] + '\n')
		#fid.write(sItem['lng'] + ' ' + sItem['lat'] + '\n')
		hxs = HtmlXPathSelector(response)
		
		#------parse the name and link of each dish
		
		dishInfoScriptList = hxs.select('//div[@id="shop-tabs"]//script[@type="text/panel"]').extract()
		
		if not dishInfoScriptList:
			return
		dishItems = []

		dishInfoList = re.findall(r'class="item" href="/shop/\w+/dish-\W+"',dishInfoScriptList[0])
		
		for dishInfo in dishInfoList:
			item = DishItem()
			dishTitlePre = re.search(r'dish-',dishInfo)				
				
			item['name'] = dishInfo[dishTitlePre.end() : len(dishInfo)-1]
			
			item['link'] = response.url + '/photos/tag-²Ë-' + item['name']
			dishItems.append(item)
			
			#fid.write(item['name'] + '\n')
		#fid.close()
		
		for item in dishItems:
			pageIdx = 1
			imgIdx = 1
			yield Request(url = item['link'], meta={'rootUrl': item['link'], 'dishName': item['name'], 'pageIdx': pageIdx, 'imgIdx': imgIdx}, callback = self.parse_img)
				
	def parse_img(self, response):
			
		hxs = HtmlXPathSelector(response)
		imgUrlList = hxs.select('//div[@class="picture-list"]//img/@src').extract()
			
		restName = hxs.select('//div[@class="crumb"]//strong/a/text()').extract()[0]
		dishName = hxs.select('//div[@class="dish-name"]/h1/text()').extract()[0]
		#fid = open('imgUrl.txt','a')
		
		if not imgUrlList:
			print restName + '-' + dishName + ': crawling finished'
			return
		
		#------create image folder
		
		dstFolderDir = self.IMG_ROOT_DIR + '\\' + restName + '\\' + dishName
		if not os.path.isdir(dstFolderDir):
			os.makedirs(dstFolderDir)
		
		#------print the index of page
		
		pageIdx = response.meta['pageIdx']
		print restName + '-' + dishName + '-pageIdx: ' + str(pageIdx)
		
		#------retrieve images using url
		
		imgIdx = response.meta['imgIdx']
		for imgUrl in imgUrlList:
			idx = imgUrl.find(self.SMALL_IMG_SIZE_STR)
			largeImgUrl = imgUrl.replace(self.SMALL_IMG_SIZE_STR, self.LARGE_IMG_SIZE_STR)
			print largeImgUrl
			#fid.write(largeImgUrl + '\n')
			
			dstPath = dstFolderDir + '\\' + str(imgIdx) + '.jpg'
			if not os.path.exists(dstPath):
				urllib.urlretrieve(largeImgUrl, dstPath)
			imgIdx += 1
		#fid.close()
		
		pageIdx = response.meta['pageIdx'] + 1
		dishImgPageUrl = response.meta['rootUrl'] + '?pg=%d' %pageIdx
		yield Request(url = dishImgPageUrl, \
			meta={'rootUrl': response.meta['rootUrl'], \
			'pageIdx': pageIdx, \
			'imgIdx': imgIdx}, \
			callback = self.parse_img)