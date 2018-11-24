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
	with open('photo_titles_dc.csv', 'wb') as res_file:
		for item in results:
			res_file.write(item)
			res_file.write('\n')


def review_photo_titles():
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
			
				#Find the last page of reviews for a given hotel
				#for link in soup.find_all('a', {'class': ['last', 'pageNum']}):
				#	page_number = link.get('data-page-number')
					#print('**********', page_number)
				#	last_offset_rev = int(page_number) * 5
				
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

					for idx, review in enumerate(soup.find_all('div', class_='review-container')):
						photo_present = review.findAll('div', {'class': 'photoContainer'})
						if photo_present:
							if soup.find('h1', {'class': 'ui_header'}) != None:
								item = {
									'hotel_name': soup.find('h1', {'class': 'ui_header'}).text,#soup.find('h1', class_='heading_title'),
									'review_title': review.find('span', class_='noQuotes').text,
									'review_body': review.find('p', class_='partial_entry').text,
									#'review_date': review.find('span', class_='relativeDate')['title'],#.text,#[idx],
									'num_reviews_reviewer': review.find('span', class_='badgetext').text,
									#'reviewer_name': review.find('span', class_='scrname').text,
									#'bubble_rating': review.select_one('div.reviewItemInline span.ui_bubble_rating')['class'][1][7:],
								}
							else:
								item = {
									'hotel_name': 'None',
									'review_title': review.find('span', class_='noQuotes').text,
									'review_body': review.find('p', class_='partial_entry').text,
									#'review_date': review.find('span', class_='relativeDate')['title'],#.text,#[idx],
									'num_reviews_reviewer': review.find('span', class_='badgetext').text,
									#'reviewer_name': review.find('span', class_='scrname').text,
									#'bubble_rating': review.select_one('div.reviewItemInline span.ui_bubble_rating')['class'][1][7:],
								}

							print(item)
							results.append(item) # <--- add to global list
							#~ yield item
							#for key,val in item.items():
								#print(key, ':', val)
							#print('----')
	return results


results = review_photo_titles()
hotel_info_to_csv(results)

