import decimal

from hotspot.models import ClusterModel, HotspotModel
from hotspot import cluster

with open("./scripts/inject.html","r") as myfile:
    data = myfile.read().replace('\n','')

geo_lat = 47.2626886
geo_long = 11.3779666

hotspot = HotspotModel()
hotspot.cluster = cluster._cluster(geo_lat, geo_long)
hotspot.name = data
hotspot.score = decimal.Decimal(100)
hotspot.category = 3
hotspot.geo_lat = geo_lat
hotspot.geo_long = geo_long
hotspot.save()
