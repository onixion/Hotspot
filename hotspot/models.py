import os
import uuid
import math
import enum
import datetime
import decimal

from django.db import models
from django.db.models.signals import post_save, pre_init
from django.dispatch import receiver
from django import forms
from django.contrib import admin
from django.utils import timezone
 
from . import settings

########################################################
## CLUSTER MODEL

CLUSTERS_LIMIT  = 50
CLUSTERS_UPDATE = 20

# geo_lat
CLUSTER_HEIGHT = decimal.Decimal(0.1)
CLUSTER_HEIGHT_HALF = CLUSTER_HEIGHT / decimal.Decimal(2)
CLUSTER_HEIGHT_QUARTER = CLUSTER_HEIGHT_HALF / decimal.Decimal(2)
CLUSTER_HEIGHT_ROUND = 1

# geo_long
CLUSTER_WIDTH = decimal.Decimal(0.1)
CLUSTER_WIDTH_HALF = CLUSTER_WIDTH / decimal.Decimal(2)
CLUSTER_WIDTH_QUARTER = CLUSTER_WIDTH_HALF / decimal.Decimal(2)
CLUSTER_WIDTH_ROUND = 1

CLUSTER_UPDATE_DELTA = datetime.timedelta(hours=2) # after 2 hours, cluster dirty
CLUSTER_UPDATE_REQUESTS = 1000 # after 1000 requests, cluster dirty

class ClusterModel(models.Model):

	uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	geo_lat  = models.DecimalField(default=0, max_digits=12, decimal_places=6)
	geo_long = models.DecimalField(default=0, max_digits=12, decimal_places=6)
	
	top          = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	left_top     = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	left         = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	left_bottom  = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	right_top    = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	right        = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	right_bottom = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)
	bottom       = models.ForeignKey("ClusterModel", on_delete=models.DO_NOTHING, related_name="+", blank=True, null=True)

	updated = models.PositiveIntegerField(default=0)         # times this cluster updated
	last_update = models.DateTimeField(default=timezone.now) # date and time of last update
	total_requests = models.PositiveIntegerField(default=0)  # total requests
	requests = models.PositiveIntegerField(default=0)        # requests since last update

	#class Meta:
	#	unique_together = (("geo_lat","geo_long"))

	def __str__(self):
		return "Cluster[" + str(self.geo_lat) + "," + str(self.geo_long) + "]"

	def dirty(self):
		b = (timezone.now() + CLUSTER_UPDATE_DELTA < self.last_update ) or \
		(self.requests >= CLUSTER_UPDATE_REQUESTS) or \
		(self.updated == 0)
		return b

	def get_left_top(self):
		geo_lat  = self.geo_lat  - CLUSTER_HEIGHT_QUARTER
		geo_long = self.geo_long - CLUSTER_WIDTH_QUARTER
		return geo_lat, geo_long

	def get_right_top(self):
		geo_lat  = self.geo_lat  - CLUSTER_HEIGHT_QUARTER
		geo_long = self.geo_long + CLUSTER_WIDTH_QUARTER
		return geo_lat, geo_long

	def get_left_bottom(self):
		geo_lat  = self.geo_lat  + CLUSTER_HEIGHT_QUARTER
		geo_long = self.geo_long - CLUSTER_WIDTH_QUARTER
		return geo_lat, geo_long

	def get_right_bottom(self):
		geo_lat  = self.geo_lat  + CLUSTER_HEIGHT_QUARTER
		geo_long = self.geo_long + CLUSTER_WIDTH_QUARTER
		return geo_lat, geo_long

class ClusterModelAdmin(admin.ModelAdmin):
	model = ClusterModel
	list_display = ['geo_lat', 'geo_long', 'updated', 'last_update', 'total_requests', 'requests' ]

admin.site.register(ClusterModel, ClusterModelAdmin)

########################################################
## HOTSPOT MODEL

HOTSPOTMODEL_CATEGORY_CHOICES = (
	(0, "Unknown"),
	(1, "Hotel"),
	(2, "Food & Restaurant"),
	(3, "Entertainment"),
	(4, "Shop"),
	(5, "Travel"),
)

class HotspotModel(models.Model):

	uuid     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	
	cluster  = models.ForeignKey(ClusterModel, on_delete=models.DO_NOTHING, related_name="hotspots", null=False, db_index=True)
	name     = models.CharField(max_length=2048, blank=False, null=False)
	geo_lat  = models.DecimalField(max_digits=12, decimal_places=6)
	geo_long = models.DecimalField(max_digits=12, decimal_places=6)
	category = models.PositiveIntegerField(default=0, null=False, blank=False, choices=HOTSPOTMODEL_CATEGORY_CHOICES)

	desc     = models.CharField(max_length=2048, blank=False, null=True)
	image    = models.URLField(max_length=2048,  blank=False, null=True)

	country  = models.CharField(max_length=2048, blank=False, null=True)
	city     = models.CharField(max_length=2048,  blank=False, null=True)
	zip      = models.CharField(max_length=2048,  blank=False, null=True)
	street   = models.CharField(max_length=2048, blank=False, null=True)
	phone    = models.CharField(max_length=2048, blank=False, null=True)
	url      = models.URLField(max_length=2048,  blank=False, null=True)
	url_fb   = models.URLField(max_length=2048,  blank=False, null=True)

	score    = models.DecimalField(max_digits=6, decimal_places=3, default=0)     # from 0 to 100
	plausibility = models.DecimalField(max_digits=6, decimal_places=3, default=0) # from 0 to 100
	updated = models.PositiveIntegerField(default=0) # times updated

	def __str__(self):
		return "Hotspot[" + str(self.name) + "|" + str(self.score) + "]"

	# calculate distance between this and a other hotspot in meters
	def distance(self, hotspot):
		geo_lat = math.radians(self.geo_lat - hotspot.geo_lat)
		geo_long = Math.toRadians(self.geo_long - hotspot.geo_long)
		a = math.sin(geo_lat/2) * math.sin(geo_lat/2) + \
			math.cos(math.radians(hotspot.geo_lat)) * math.cos(math.radians(selft.geo_lat)) * \
			math.sin(geo_long/2) * Math.sin(geo_long/2)
		return 6371000 * math.atan2(math.sqrt(a), math.sqrt(1-a))

class HotspotScoreModel(models.Model):
	uuid		= models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	spot		= models.ForeignKey(HotspotModel, default=None,	null=True, on_delete=models.CASCADE, db_index=True)
	#spot_uuid	= models.UUIDField(primary_key=False, editable=True)
	score_type	= models.PositiveIntegerField(default=0)
	score		= models.PositiveIntegerField(default=0)
	score_weight	= models.PositiveIntegerField(default=0)


class HotspotScoreModelAdmin(admin.ModelAdmin):
	model = HotspotScoreModel
	list_display = ['spot', 'score_type', 'score', 'score_weight' ]

#inline Score editing in hotspotmodel
class HotspotScoreModelInline(admin.TabularInline):
	model = HotspotScoreModel
	max_num = 2
	
admin.site.register(HotspotScoreModel, HotspotScoreModelAdmin)

class HotspotModelAdmin(admin.ModelAdmin):
	model = HotspotModel
	list_display = ['uuid', 'name', 'desc', 'category', 'score', 'plausibility' ] 
	inlines = [ HotspotScoreModelInline ]

admin.site.register(HotspotModel, HotspotModelAdmin)

class ScoreType(enum.Enum):
	Facebook = 1
	Yelp = 2

class HotspotType(enum.Enum):
	UNKNOWN = 0
	HOTEL_LODGING = 1
	FOOD_BEVERAGE = 2
	ARTS_ENTERTAINMENT = 3
	SHOPPING_RETAIL = 4
	TRAVEL_TRANSPORTATION = 5

	def __str__(self):
		return hotspot_type_string[self]

	def parse(string):
		string = string.lower().strip()

		# if it is in the dict, return type
		if string in hotspot_type_lookup:
			return hotspot_type_lookup[string].value

		# if not try each entry
		else:
			# the first substring in lookup dict. wins
			for key in hotspot_type_lookup:
				if key in string:
					return hotspot_type_lookup[key].value

			return HotspotType.UNKNOWN.value

hotspot_type_string = \
{
	HotspotType.UNKNOWN:               "UNKNOWN",
	HotspotType.HOTEL_LODGING:         "HOTEL_LODGING",
	HotspotType.FOOD_BEVERAGE:         "FOOD_BEVERAGE",
	HotspotType.ARTS_ENTERTAINMENT:    "ARTS_ENTERTAINMENT",
	HotspotType.SHOPPING_RETAIL:       "SHOPPING_RETAIL",
	HotspotType.TRAVEL_TRANSPORTATION: "TRAVEL_TRANSPORTATION",
}

hotspot_type_lookup = \
{
	# HOTEL_LODGING
	"hotel": HotspotType.HOTEL_LODGING,
	"lodging": HotspotType.HOTEL_LODGING,

	# FOOD_BEVERAGE
	"food": HotspotType.FOOD_BEVERAGE,
	"beverage": HotspotType.FOOD_BEVERAGE,

	# ARTS_ENTERTAINMENT
	"arts": HotspotType.ARTS_ENTERTAINMENT,
	"entertainment": HotspotType.ARTS_ENTERTAINMENT,

	# SHOPPING_RETAIL
	"shop": HotspotType.SHOPPING_RETAIL,
	"retail": HotspotType.SHOPPING_RETAIL,

	# TRAVEL_TRANSPORTATION
	"travel": HotspotType.TRAVEL_TRANSPORTATION,
	"transport": HotspotType.TRAVEL_TRANSPORTATION,
}
