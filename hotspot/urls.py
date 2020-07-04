from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
	url(r"^admin/", admin.site.urls),
	
	# VIEWS
	url(r"^$", views.index),


	# API
	url(r"^api/hotspots/$", views.api_hotspots),
	url(r"^api/hotspots/area/$", views.api_hotspots_area),
	url(r"^api/hotspot/$", views.api_hotspot),
	url(r"^api/hotspot/content/$", views.api_hotspot_content),
	
	url(r"^api/clusters/$", views.api_clusters),
	url(r"^api/clusters/grid/$", views.api_clusters_grid),
]
