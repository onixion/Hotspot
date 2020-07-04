import decimal

from hotspot import models, cluster

clusters = models.ClusterModel.objects.all()

cluster_count = 0

for i, cluster in enumerate(clusters):
	
	print("CLUSTER " + str(i))
	print("  uuid:           " + str(cluster.uuid))
	print("  geo:            " + str(cluster.geo_lat) + "," + str(cluster.geo_long))
	print("  updated:        " + str(cluster.updated))
	print("  requests:       " + str(cluster.requests))
	print("  total_requests: " + str(cluster.total_requests))
	print("  last_update:    " + str(cluster.last_update))
	print("  neighbors:")
	print("    top:          " + str(cluster.top))
	print("    left_top:     " + str(cluster.left_top))
	print("    right_top:    " + str(cluster.right_top))
	print("    bottom:       " + str(cluster.bottom))
	print("    left_bottom:  " + str(cluster.left_bottom))
	print("    right_bottom: " + str(cluster.right_bottom))
	print("    left:         " + str(cluster.left))
	print("    right:        " + str(cluster.right))

	hotspot_count = 0
	
	for hotspot in cluster.hotspots.all():

		#print("    Hotspot: " + str(hotspot.uuid))
		hotspot_count = hotspot_count + 1

	print("  hotspots:       " + str(hotspot_count))
	print("")

	cluster_count = cluster_count + 1

print("clusters total: " + str(cluster_count))
