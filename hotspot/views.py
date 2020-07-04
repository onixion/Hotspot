import os
import datetime
import threading
import decimal
import math
import numpy
import random

from django import http, template
from django.http import HttpResponse, JsonResponse

from django.template.response import TemplateResponse
from django.template import TemplateDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone, html

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from ratelimit.utils import is_ratelimited

from . import models, serializers, fetcher
from . import cluster as cl

# ------------------- VIEW ----------------------------

def index(request):
	return TemplateResponse(request, "index.html")

# ------------------- API -----------------------------

API_REQUEST_LIMIT = "1000/h"

def api_hotspots(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	hotspots = reversed(models.HotspotModel.objects.order_by("score"))

	data = {}
	data["type"] = "FeatureCollection"
	data["features"] = []

	for hotspot in hotspots:

		tmp = {}
		tmp["type"] = "Feature"
		tmp["geometry"] = {}
		tmp["geometry"]["type"] = "Point"
		tmp["geometry"]["coordinates"] = [hotspot.geo_long, hotspot.geo_lat]
		tmp["properties"] = {}
		tmp["properties"]["name"] = html.escape(hotspot.name)
		tmp["properties"]["uuid"] = str(hotspot.uuid)
		tmp["properties"]["desc"] = html.escape(hotspot.desc)
		tmp["properties"]["score"] = hotspot.score
		tmp["properties"]["plausibility"] = hotspot.plausibility
		tmp["properties"]["image"] = html.escape(hotspot.image)
		tmp["properties"]["url"] = html.escape(hotspot.url)
		tmp["properties"]["category"] = hotspot.category
		data["features"].append(tmp)

	return HttpResponse(status=200, content_type="application/json",
		content=JSONRenderer().render(data))

def api_hotspot(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	if "uuid" in request.GET:
		uuid = request.GET["uuid"]
	else:
		return HttpResponse(status=404)

	hotspot = models.HotspotModel.objects.filter(uuid=uuid).first()
	if hotspot is None:
		return HttpResponse(status=404)

	return HttpResponse(status=200, content_type="application/json",
		content=JSONRenderer().render(serializers.HotspotSerializer(hotspot).data))

def api_hotspot_content(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	if "uuid" in request.GET:
		uuid = request.GET["uuid"]
	else:
		return HttpResponse(status=404)

	hotspot = models.HotspotModel.objects.filter(uuid=uuid).first()
	if hotspot is None:
		return HttpResponse(status=404)

	return TemplateResponse(request, "details.html", {"hotspot":hotspot})

def api_clusters(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	clusters = models.ClusterModel.objects.all()

	data = {}
	data["type"] = "FeatureCollection"
	data["features"] = []

	for cluster in clusters:

		tmp = {}
		tmp["type"] = "Feature"
		tmp["geometry"] = {}
		tmp["geometry"]["type"] = "Point"
		tmp["geometry"]["coordinates"] = [cluster.geo_long, cluster.geo_lat]
		tmp["properties"] = {}
		data["features"].append(tmp)

	return HttpResponse(status=200, content_type="application/json",
		content=JSONRenderer().render(data))

def api_clusters_grid(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	data = {}
	data["type"] = "FeatureCollection"
	data["features"] = []

	geo_lat = decimal.Decimal(-90)

	while True:
		tmp = {}
		tmp["type"] = "Feature"
		tmp["geometry"] = {}
		tmp["geometry"]["type"] = "LineString"
		tmp["geometry"]["coordinates"] = [
			[-180-models.CLUSTER_WIDTH_HALF, geo_lat-models.CLUSTER_HEIGHT_HALF],
			[ 180-models.CLUSTER_WIDTH_HALF, geo_lat-models.CLUSTER_HEIGHT_HALF]]
		data["features"].append(tmp)
		geo_lat += models.CLUSTER_HEIGHT
		if geo_lat > 90: break

	geo_long = decimal.Decimal(-180)

	while True:
		tmp = {}
		tmp["type"] = "Feature"
		tmp["geometry"] = {}
		tmp["geometry"]["type"] = "LineString"
		tmp["geometry"]["coordinates"] = [
			[geo_long-models.CLUSTER_WIDTH_HALF, -90-models.CLUSTER_HEIGHT_HALF],
			[geo_long-models.CLUSTER_WIDTH_HALF,  90-models.CLUSTER_HEIGHT_HALF]]
		data["features"].append(tmp)
		geo_long += models.CLUSTER_WIDTH
		if geo_long > 180: break

	return HttpResponse(status=200, content_type="application/json",
		content=JSONRenderer().render(data))

def api_hotspots_area(request):

	if is_ratelimited(request, key="ip", rate=API_REQUEST_LIMIT, group="api", increment=True):
		return HttpResponse(status=429)

	geo_lat = None
	geo_long = None
	geo_lat2 = None
	geo_long2 = None
	filter = []

	if "geo_lat" in request.GET:
		geo_lat = decimal.Decimal(request.GET["geo_lat"])
	if "geo_long" in request.GET:
		geo_long = decimal.Decimal(request.GET["geo_long"])
	if "geo_lat2" in request.GET:
		geo_lat2 = decimal.Decimal(request.GET["geo_lat2"])
	if "geo_long2" in request.GET:
		geo_long2 = decimal.Decimal(request.GET["geo_long2"])
	if "filter" in request.GET:
		if len(request.GET["filter"]) is not 0:
			filter = [ int(x) for x in request.GET["filter"].split(",") ]

	if (geo_lat is None) or (geo_long is None) or \
		(geo_lat2 is None)  or (geo_long2 is None):
		return HttpResponse(status=404)

	# get center geo location
	geo_lat_center = round((geo_lat + geo_lat2) / 2, models.CLUSTER_HEIGHT_ROUND)
	geo_long_center = round((geo_long + geo_long2) / 2, models.CLUSTER_WIDTH_ROUND)

	# get corner geo location
	geo_lat2 = round(geo_lat2, models.CLUSTER_HEIGHT_ROUND)
	geo_long2 = round(geo_long2, models.CLUSTER_WIDTH_ROUND)

	# get size of view in cluster units
	n_height = math.ceil(abs(geo_lat-geo_lat2)/models.CLUSTER_HEIGHT)
	n_width = math.ceil(abs(geo_long-geo_long2)/models.CLUSTER_WIDTH)

	clusters_count =  n_width * n_height

	if clusters_count <= models.CLUSTERS_LIMIT:

		update = clusters_count <= models.CLUSTERS_UPDATE
		cluster_center = cl.get_cluster(geo_lat_center, geo_long_center, update)
		clusters = cl.get_clusters(
			cluster_center,
			math.ceil((n_width)/2), math.ceil((n_height)/2),
			update)

	else: clusters = []

	data = {}
	data["type"] = "FeatureCollection"
	data["features"] = []

	for cluster in clusters:

		#------------------------------
		# FOR TESTING ONLY
		#tmp = {}
		#tmp["type"] = "Feature"
		#tmp["geometry"] = {}
		#tmp["geometry"]["type"] = "Point"
		#tmp["geometry"]["coordinates"] = [cluster.geo_long, cluster.geo_lat]
		#tmp["properties"] = {}
		#data["features"].append(tmp)
		#continue
		#------------------------------

		# filter for categories
		if len(filter) is 0: hotspots = cluster.hotspots.all()
		else: hotspots = cluster.hotspots.filter(category__in=filter)

		# order by score and limit to hotspots per cluster
		#if hotposts_per_cluster is -1: hotspots = hotspots.order_by("score")
		#else: hotspots = hotspots.order_by("score")[:hotposts_per_cluster]

		hotspots = hotspots.order_by("score")

		for hotspot in hotspots:

			tmp = {}
			tmp["type"] = "Feature"
			tmp["geometry"] = {}
			tmp["geometry"]["type"] = "Point"
			tmp["geometry"]["coordinates"] = [hotspot.geo_long, hotspot.geo_lat]
			
			tmp["properties"] = {}
			tmp["properties"]["name"] = html.escape(hotspot.name)
			tmp["properties"]["uuid"] = str(hotspot.uuid)
			tmp["properties"]["desc"] = html.escape(hotspot.desc)
			tmp["properties"]["score"] = hotspot.score
			tmp["properties"]["plausibility"] = hotspot.plausibility
			tmp["properties"]["image"] = html.escape(hotspot.image)
			tmp["properties"]["url"] = html.escape(hotspot.url)
			tmp["properties"]["category"] = hotspot.category

			data["features"].append(tmp)

	return HttpResponse(status=200, content_type="application/json",
		content=JSONRenderer().render(data))
