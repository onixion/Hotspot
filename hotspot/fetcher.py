import decimal
import random
import math

from . import models
from . import cluster as cl

import facebook
from yelpapi import YelpAPI

facebook_id = "1999169076963381"
facebook_secret = "b74a67557d9ef29996ba62f1efd5da2b"
facebook_access_token = ""
yelp_id = "YOCKC43okxk42-5wfphiDg"
yelp_secret = "eqXIzcF7RZHMBo0XzVD5jYXZps39s5HYDH22lTNtAceGEbBI9oeUUgLuPFbgVfKA"

# aquire facebook access token
def fetch_facebook_access_token():

	graph = facebook.GraphAPI()
	result = graph.request("/oauth/access_token?client_id=" + facebook_id + 
		"&client_secret=" + facebook_secret + "&grant_type=client_credentials")
	global facebook_access_token
	facebook_access_token = result["access_token"]
	#print("facebook access_token: " + facebook_access_token)

def calculate_total_score(hotspot):
	MAX_PLAUSIBILITY = 100
	total_weight = 0
	score_weighted = 0
	
	all_scores = models.HotspotScoreModel.objects.filter( spot = hotspot )
	
	for score in all_scores:
		score_weighted = score_weighted + score.score * score.score_weight
		total_weight = total_weight + score.score_weight
	if total_weight == 0:
		hotspot.score = 0
	else:
		hotspot.score = score_weighted / total_weight
	
	hotspot.plausibility = math.log(total_weight + 1, 10) * 37
	if hotspot.plausibility > MAX_PLAUSIBILITY:
	   hotspot.plausibility = MAX_PLAUSIBILITY
	   
	hotspot.score = hotspot.score * hotspot.plausibility / MAX_PLAUSIBILITY * 2 #normalize score 0-100

def create_score_object(hotspot, type_value):
	try:
		hotspot_score = models.HotspotScoreModel.objects \
				.get( \
					spot=hotspot,
					score_type=type_value \
				)
		# if the hotspot does not exist, create it
	except models.HotspotScoreModel.DoesNotExist:
		hotspot_score = models.HotspotScoreModel()
		hotspot_score.spot	 = hotspot
		hotspot_score.score_type = type_value
	return hotspot_score

def fetch_facebook(cluster):

	fetch_facebook_access_token()
	graph = facebook.GraphAPI(access_token=facebook_access_token)

	# get places
	for i in range(0,4):

		try:
			if   i is 0: geo_lat, geo_long = cluster.get_left_top()
			elif i is 1: geo_lat, geo_long = cluster.get_right_top()
			elif i is 2: geo_lat, geo_long = cluster.get_left_bottom()
			elif i is 3: geo_lat, geo_long = cluster.get_right_bottom()

			result = graph.request("/search?" + 
				"access_token=" + facebook_access_token + 
				"&type=place" +
				"&center=" + str(geo_lat) + "," + str(geo_long) +
				"&distance=4000" +
				#"&q=food"
				"&limit=500" +
				"&categories=['HOTEL_LODGING','FOOD_BEVERAGE','ARTS_ENTERTAINMENT','SHOPPING_RETAIL','TRAVEL_TRANSPORTATION']"
				"&fields=id,name,location,picture,about,phone,category,website" + 
				",overall_star_rating,rating_count,talking_about_count,checkins,fan_count,were_here_count,is_permanently_closed" +
				",matched_categories")

			created = 0
			updated = 0
			ignored = 0

			for place in result["data"]:
			
				# check if we have a hotspot with the exact same
				# geo location
				geo_lat = decimal.Decimal(place["location"]["latitude"])
				geo_long = decimal.Decimal(place["location"]["longitude"])

				if geo_lat is None or geo_long is None: continue

				# ignore places, which are not inside the cluster
				if not cl.is_inside_cluster(cluster, geo_lat, geo_long):
					ignored = ignored + 1
					continue
					
				#ignore permanetly closed places
				if "is_permanently_closed" in place:
					if place["is_permanently_closed"]:
						ignored = ignored + 1
						continue

				# create hotspot, if it does not exist
				hotspot = models.HotspotModel.objects \
					.filter( \
						name=place["name"],
						geo_lat__range=(geo_lat-models.CLUSTER_HEIGHT_HALF,geo_lat+models.CLUSTER_HEIGHT_HALF),
						geo_long__range=(geo_long-models.CLUSTER_WIDTH_HALF,geo_long+models.CLUSTER_WIDTH_HALF)) \
					.first()

				# if the hotspot does not exist, create it
				if hotspot is None:

					hotspot = models.HotspotModel()
					hotspot.cluster = cluster
					hotspot.name = place["name"]
					hotspot.geo_lat = geo_lat
					hotspot.geo_long = geo_long
					created += 1

				else:

					updated += 1

				if "about" in place:
					if place["about"] is not None:
						hotspot.desc = place["about"]

				if "matched_categories" in place:
					#hotspot.category = models.HotspotType.parse(place["category"])
					if place["matched_categories"][0] is not None:
						hotspot.category = models.HotspotType.parse(place["matched_categories"][0])

				if "country" in place["location"]:
					if place["location"]["country"] is not None:
						hotspot.country = place["location"]["country"]

				if "city" in place["location"]:
					if place["location"]["city"] is not None:
						hotspot.city = place["location"]["city"]

				if "zip" in place["location"]:
					if place["location"]["zip"] is not None:
						hotspot.zip = place["location"]["zip"]

				if "street" in place["location"]:
					if place["location"]["street"] is not None:
						hotspot.street = place["location"]["street"]

				if "phone" in place:
					if place["phone"] is not None:
						hotspot.phone = place["phone"]

				if "data" in place["picture"]:
					if "url" in place["picture"]["data"]:
						if place["picture"]["data"]["url"] is not None:
							hotspot.image = place["picture"]["data"]["url"]

				if "website" in place:
					if place["website"] is not None:
						hotspot.url = place["website"]

				if "link" in place:
					if place["link"] is not None:
						hotspot.url_fb = place["link"]

				# calculating score by facebooks rating system

				#Rating from 1, 1.5, 2.0, ... 5.0 -> 10, 15 ... 50
				overall_star_rating = 0
				if "overall_star_rating" in place:
					overall_star_rating = place["overall_star_rating"] * 10

				# number of ratings given
				rating_count = 0
				if "rating_count" in place:
					rating_count = place["rating_count"]

				# number of people talking about this
				talking_about_count = 0
				if "talking_about_count" in place:
					talking_about_count = place["talking_about_count"]

				# checkins
				checkins = 0
				if "checkins" in place:
					checkins = place["checkins"]

				# fan_count
				fan_count = 0
				if "fan_count" in place:
					fan_count = place["fan_count"]

				# were_here_count
				were_here_count = 0
				if "were_here_count" in place:
					were_here_count = place["were_here_count"]

				hotspot.updated += 1
				
				hotspot.score = 0
				hotspot.save()
				
				hotspot_score = create_score_object(hotspot, models.ScoreType.Facebook.value)
					
				hotspot_score.score = overall_star_rating
				hotspot_score.score_weight = rating_count
				hotspot_score.save()

		except:
			pass

	return created, updated

def fetch_yelp(cluster):
	yelp_api = YelpAPI(yelp_id, yelp_secret)

	created = 0
	updated = 0
	ignored = 0
	
	category_map = { 
		"food,restaurants" : models.HotspotType.FOOD_BEVERAGE,
		"hotelstravel" : models.HotspotType.HOTEL_LODGING,
		"arts,nightlife" : models.HotspotType.ARTS_ENTERTAINMENT,
		"shopping" : models.HotspotType.SHOPPING_RETAIL
	}
	#["food,restaurants","hotelstravel","arts,nightlife","shopping"]
	for category, category_value in category_map.items():

		result = yelp_api.search_query(longitude=cluster.geo_long, latitude=cluster.geo_lat, limit=50, \
					       categories=[category])

		for business in result["businesses"]:

			# if coordinates are missing ignore this business
			if "coordinates" not in business: continue
			if "latitude" not in business["coordinates"]: continue
			if "longitude" not in business["coordinates"]: continue

			geo_lat = decimal.Decimal(business["coordinates"]["latitude"])
			geo_long = decimal.Decimal(business["coordinates"]["longitude"])

			if not cl.is_inside_cluster(cluster, geo_lat, geo_long) or business["is_closed"]:
				ignored = ignored + 1
				continue

			#TODO: fix hotspot matching
			hotspot = models.HotspotModel.objects \
				.filter( \
				name=business["name"],
				geo_lat__range=(geo_lat - models.CLUSTER_HEIGHT_HALF, geo_lat + models.CLUSTER_HEIGHT_HALF),
				geo_long__range=(geo_long - models.CLUSTER_WIDTH_HALF, geo_long + models.CLUSTER_WIDTH_HALF)) \
				.first()

			if hotspot is None:
				hotspot = models.HotspotModel()
				hotspot.cluster = cluster
				hotspot.name = business["name"]
				hotspot.geo_lat = geo_lat
				hotspot.geo_long = geo_long
				hotspot.category = category_value.value
				created += 1
				#print("creation: " + business["name"])
			else:
				updated += 1
				#print("update: " + business["name"])

			if "country" in business["location"] and hotspot.country is None:
				hotspot.country = business["location"]["country"]

			if "city" in business["location"] and hotspot.city is None:
				hotspot.city = business["location"]["city"]

			#Rating from 1, 1.5, 2.0, ... 5.0 -> 10, 15 ... 50
			rating = 0
			if "rating" in business:
				rating = business["rating"] * 10    

			review_count = 0
			#Rating in yelp counts more
			if "review_count" in business:
				review_count = business["review_count"] * 3

			hotspot.updated += 1

			hotspot.save()

			hotspot_score = create_score_object(hotspot, models.ScoreType.Yelp.value)

			hotspot_score.score = rating
			
			#higher weight for yelp, because review is more work than just a like
			hotspot_score.score_weight = review_count * 10
			hotspot_score.save()

	return created, updated
    
def calculate_total_score_4_cluster_hotspots(cluster):
    
	for hotspot in models.HotspotModel.objects \
			.filter( cluster = cluster ):
		calculate_total_score(hotspot)
		hotspot.save()
		