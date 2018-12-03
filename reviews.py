import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
import ssl
import json
import re
import sys
import warnings 
import requests
import csv
from lxml import html

if not sys.warnoptions:
	warnings.simplefilter("ignore")#For ignoring SSL certificate errors
	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE# url = input('Enter url - ' )


def hotel_info_to_json(soup):
	hotel_json = {}
	for line in soup.find_all('script',attrs={"type" : "application/ld+json"}):
		details = line.text.strip()
		details = json.loads(details)

		hotel_json["name"] = details["name"]
		details["priceRange"] = details["priceRange"].replace("₹ ","Rs ")
		details["priceRange"] = details["priceRange"].replace("₹","Rs ")
		hotel_json["priceRange"] = details["priceRange"]
		hotel_json["aggregateRating"]={}
		hotel_json["aggregateRating"]["ratingValue"]=details["aggregateRating"]["ratingValue"]
		hotel_json["aggregateRating"]["reviewCount"]=details["aggregateRating"]["reviewCount"]
		break
	hotel_json["reviews"]=[]
	for line in soup.find_all('p',attrs={"class" : "partial_entry"}):
		review = line.text.strip()
		if review != "":
			review = line.text.strip()
		if review.endswith( "More" ):
			review = review[:-4]
		if review.startswith("Dear"):
			continue
		review = review.replace('\r', ' ').replace('\n', ' ')
		review = ' '.join(review.split())
		hotel_json["reviews"].append(review)

	with open(hotel_json["name"].replace('/', '') + ".json", 'w') as outfile:
		json.dump(hotel_json, outfile, indent=4)


def hotel_info_to_csv(results):
	keys = results[0].keys()
	with open('photo_titles_dc_small.csv', 'w') as res_file:
		dict_writer = csv.DictWriter(res_file, keys)
		dict_writer.writeheader()
		dict_writer.writerows(results)


def write_item_to_csv(item):
	keys = item.keys()
	with open('photo_titles_dc_small.csv', 'a') as res_file:
		dict_writer = csv.DictWriter(res_file, keys)
		dict_writer.writerow(item)


def write_items_to_csv(list_of_items):
	print(list_of_items)
	with open('full_photo_reviews_dc.csv', 'a') as res_file:
		csv_out = csv.writer(res_file)
		csv_out.writerow(list_of_items)


def getPageReviewsWithPhoto(url):
	s = requests.Session()
	s.headers.update({
		'accept': 'text/html, */*; q=0.01',
		#'accept-encoding': 'gzip, deflate, br',
		'dnt': '1',
		'origin': 'https://www.tripadvisor.ca',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
		'pragma': 'no-cache',
		'cache-control': 'no-cache',
		'upgrade-insecure-requests': '1'
	})
	req = s.get(url)
	soup = BeautifulSoup(req.text, "html.parser")

  # collect review ids what has photo
	reviews = ''
	for review in soup.find_all("div", "reviewSelector"):
		photos = review.find_all("div", "photoContainer")
		if len(photos) > 0:
			if len(reviews) > 0 :
				reviews += ','

			reviews += review.attrs['data-reviewid']

	hotels = []
	titles = []
	items = []
	if len(reviews) > 0:
		headers = {
			'content-type': 'application/x-www-form-urlencoded',
			'referer': url
		}

		form_data = {
			'reviews': reviews,
			'contextChoice': 'DETAIL_HR',
			'loadMtHeader': 'true',
			'haveJses': 'earlyRequireDefine,amdearly,global_error,long_lived_global,apg-Hotel_Review,apg-Hotel_Review-in,bootstrap,desktop-rooms-guests-dust-en_CA,responsive-calendar-templates-dust-en_CA,responsive-heatmap-calendar-templates-dust-en_CA,@ta/common.global,@ta/tracking.interactions,@ta/public.maps,@ta/overlays.managers,@ta/overlays.headers,@ta/overlays.shift,@ta/common.overlays,@ta/overlays.toast,@ta/trips.save-to-trip,social.share-cta,@ta/trips.trip-link,@ta/media.image,cross-sells.results-from-featured,@ta/social.review-inline-follow-widget,@ta/hotels.hotel-review-new-hotel-preview,@ta/hotels.hotel-review-new-hotel-banner,@ta/common.typeahead,@ta/common.media,@ta/hotels.hotel-review-atf-photos-2018-redesign,@ta/maps.snapshot,@ta/hotels.tags,hotels.hotel-review-overview,hotels.hotel-review-roomtips,hotels.hotel-review-photos,@ta/platform.runtime,masthead_search_late_load,taevents,p13n_masthead_search__deferred__lateHandlers',
			'haveCsses': 'apg-Hotel_Review-in,responsive_calendars_corgi',
			'Action': 'install'
		}

		req = s.post('https://www.tripadvisor.ca/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS_RESP&metaReferer=', data = form_data, headers = headers)
		soup = BeautifulSoup(req.text, "html.parser")

		# remove response
		[s.extract() for s in soup('div', 'mgrRspnInline')]

		titles.append(review.find('span', class_='noQuotes').text)

		for review in soup.find_all("p", "partial_entry"):
			items.append( review.text.strip() )


	return(titles, items)


def reviews_dc():
	offset = 0
	url = 'https://www.tripadvisor.com/Hotels-g28970-oa' + str(offset) + '-Washington_DC_District_of_Columbia-Hotels.html'

	r = requests.get(url)
	soup = BeautifulSoup(r.text, "html.parser")

	#Find last page of the hotels in DC
	for link in soup.find_all('a', {'last'}):
		page_number = link.get('data-page-number')
		last_offset = int(page_number) * 30
		print('last offset:', last_offset)


	digit = lambda x: int(filter(str.isdigit, x) or 0)
	results = list()
	for offset in range(0, last_offset+1, 30):
		print('--- page offset:', offset, '---')

		url = 'https://www.tripadvisor.com/Hotels-g28970-oa' + str(offset) + '-Washington_DC_District_of_Columbia-Hotels.html'

		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")

		links = set()
		for page in soup.findAll('a', {'class': 'property_title prominent '}):
			links.add(page["href"])
		if links:
			count = 0           
			for next_page in links:
				page_response = urllib.request.urlopen("https://www.tripadvisor.com" + next_page, context=ctx).read()
				soup = BeautifulSoup(page_response,	"html.parser")
				
				last_offset_rev = 0
				for link in soup.select('a.last.pageNum'):
					if link.get('href') != '':
						last_offset_rev = int(link.text) * 5

				print("REVIEW OFFSET: ", last_offset_rev)

				for review_offset in range(0, last_offset_rev+1, 5):
					print('--- review page offset:', review_offset, '---')
					ind = next_page.find("Reviews")

					url = "https://www.tripadvisor.com" + next_page[:ind+7] + "-or" + str(review_offset) + next_page[ind+7:]
					r = requests.get(url)
					soup = BeautifulSoup(r.text, "html.parser")
					print(url)
					print("")
					items = getPageReviewsWithPhoto(url) #for one page of reviews
					res = []
					res.append(url)
					if soup.find('h1', {'class': 'ui_header'}) != None:
						res.append(soup.find('h1', {'class': 'ui_header'}).text)
					else:
						res.append("No name")
					if len(items) == 2:
						for i in items:
							res.append("".join(i))
					else:
						stringt = ''
						c = 0
						for i in items:
							if c == 0:
								continue
							stringt += "".join(i) + ' '
							c += 0
						res.append(stringt)
					if len(items[0]) > 0:
						results.append(res)
						write_items_to_csv(res)

	return results



results = reviews_dc()
#hotel_info_to_csv(results)
