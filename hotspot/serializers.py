from rest_framework import serializers

from . import models

class HotspotSerializer(serializers.Serializer):
	
	uuid     = serializers.UUIDField(required=True)

	name     = serializers.CharField(max_length=128, required=True)
	geo_lat  = serializers.DecimalField(max_digits=12, decimal_places=6, required=True)
	geo_long = serializers.DecimalField(max_digits=12, decimal_places=6, required=True)
	category = serializers.ChoiceField(models.HOTSPOTMODEL_CATEGORY_CHOICES, required=True)

	desc     = serializers.CharField(max_length=256, required=False)
	image    = serializers.URLField(max_length=256, required=False)

	country  = serializers.CharField(max_length=128, required=False)
	city     = serializers.CharField(max_length=64, required=False)
	zip      = serializers.CharField(max_length=32, required=False)
	street   = serializers.CharField(max_length=128, required=False)
	phone    = serializers.CharField(max_length=32, required=False)
	url      = serializers.URLField(max_length=256, required=False)
	url_fb   = serializers.URLField(max_length=256, required=False)

	score = serializers.IntegerField(required=True)
	plausibility = serializers.IntegerField(required=True)