import requests
from bs4 import BeautifulSoup

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

    for review in soup.find_all("p", "partial_entry"):
      items.append( review.text.strip() )

  return items


items = getPageReviewsWithPhoto('https://www.tripadvisor.com/Hotel_Review-g298314-d6650543-Reviews-CAPSULE_by_Container_Hotel-Sepang_Sepang_District_Selangor.html')
print(items)
