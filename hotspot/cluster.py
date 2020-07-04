import os
import datetime
import threading
import time
import traceback
import decimal
import queue

from django.utils import timezone

from . import models, serializers, fetcher, cluster

CLUSTER_WORKER = 4

cluster_neighbors = [
	( models.CLUSTER_HEIGHT, 0),                    # top:          0
	( models.CLUSTER_HEIGHT,-models.CLUSTER_WIDTH), # left top:     1 
	( 0,                    -models.CLUSTER_WIDTH), # left:         2
	(-models.CLUSTER_HEIGHT,-models.CLUSTER_WIDTH), # left bottom:  3
	( models.CLUSTER_HEIGHT, models.CLUSTER_WIDTH), # right top:    4
	( 0,                     models.CLUSTER_WIDTH), # right:        5
	(-models.CLUSTER_HEIGHT, models.CLUSTER_WIDTH), # right bottom: 6
	(-models.CLUSTER_HEIGHT, 0),                    # bottom:       7
]

def _cluster(geo_lat, geo_long):

	geo_lat  = round(decimal.Decimal(geo_lat),  models.CLUSTER_HEIGHT_ROUND)
	geo_long = round(decimal.Decimal(geo_long), models.CLUSTER_WIDTH_ROUND)

	cluster = models.ClusterModel.objects.filter(
		geo_lat=geo_lat,
		geo_long=geo_long).first()

	if cluster is None:

		cluster = models.ClusterModel()
		cluster.geo_lat = geo_lat
		cluster.geo_long = geo_long
		cluster.updated = 0
		cluster.last_update = timezone.now()
		cluster.requests = 0
		cluster.total_requests = 0
		cluster.save()

		# set neighbor cluster connections

		# top
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[0][0],
			geo_long=cluster.geo_long+cluster_neighbors[0][1]).first()
		if c is not None: 
			cluster.top = c
			c.bottom = cluster
			c.save()

		# left top
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[1][0],
			geo_long=cluster.geo_long+cluster_neighbors[1][1]).first()
		if c is not None: 
			cluster.left_top = c
			c.right_bottom = cluster
			c.save()

		# left
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[2][0],
			geo_long=cluster.geo_long+cluster_neighbors[2][1]).first()
		if c is not None: 
			cluster.left = c
			c.right = cluster
			c.save()

		# left bottom
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[3][0],
			geo_long=cluster.geo_long+cluster_neighbors[3][1]).first()
		if c is not None: 
			cluster.left_bottom = c
			c.right_top = cluster
			c.save()

		# right top
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[4][0],
			geo_long=cluster.geo_long+cluster_neighbors[4][1]).first()
		if c is not None: 
			cluster.right_top = c
			c.left_bottom = cluster
			c.save()

		# right
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[5][0],
			geo_long=cluster.geo_long+cluster_neighbors[5][1]).first()
		if c is not None: 
			cluster.right = c
			c.left = cluster
			c.save()

		# right bottom
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[6][0],
			geo_long=cluster.geo_long+cluster_neighbors[6][1]).first()
		if c is not None: 
			cluster.right_bottom = c
			c.left_top = cluster
			c.save()

		# bottom
		c = models.ClusterModel.objects.filter(
			geo_lat=cluster.geo_lat+cluster_neighbors[7][0],
			geo_long=cluster.geo_long+cluster_neighbors[7][1]).first()
		if c is not None: 
			cluster.bottom = c
			c.top = cluster
			c.save()

	return cluster

def get_cluster(geo_lat, geo_long, update):

	cluster = _cluster(geo_lat, geo_long)
	if update: _update_cluster(cluster)

	return cluster

def is_inside_cluster(cluster, geo_lat, geo_long):

	geo_lat = decimal.Decimal(geo_lat)
	geo_long = decimal.Decimal(geo_long)

	if (cluster.geo_lat - models.CLUSTER_HEIGHT_HALF) < geo_lat <= (cluster.geo_lat + models.CLUSTER_HEIGHT_HALF):
		if (cluster.geo_long - models.CLUSTER_WIDTH_HALF) < geo_long <= (cluster.geo_long + models.CLUSTER_WIDTH_HALF):
			return True
	return False

# get cluster and n rings around this cluster
def get_clusters(cluster, n_width, n_height, update):
	
	clusters = [ cluster ]

	# top
	if cluster.top is None:
		cluster_top = _get_cluster_neighbor(cluster, 0)
		if update: _update_cluster(cluster_top)
	else: cluster_top = cluster.top
	clusters += _get_clusters_top(cluster_top, n_width, n_height-1, update)

	# left top
	if cluster.left_top is None:
		cluster_left_top = _get_cluster_neighbor(cluster, 1)
		if update: _update_cluster(cluster_left_top)
	else: cluster_left_top = cluster.left_top
	clusters += _get_clusters_left_top(cluster_left_top, n_width-1, n_height-1, update)

	# left
	if cluster.left is None:
		cluster_left = _get_cluster_neighbor(cluster, 2)
		if update: _update_cluster(cluster_left)
	else: cluster_left = cluster.left
	clusters += _get_clusters_left(cluster_left, n_width-1, n_height, update)

	# left bottom
	if cluster.left_bottom is None:
		cluster_left_bottom = _get_cluster_neighbor(cluster, 3)
		if update: _update_cluster(cluster_left_bottom)
	else: cluster_left_bottom = cluster.left_bottom
	clusters += _get_clusters_left_bottom(cluster_left_bottom, n_width, n_height-1, update)

	# right top
	if cluster.right_top is None:
		cluster_right_top = _get_cluster_neighbor(cluster, 4)
		if update: _update_cluster(cluster_right_top)
	else: cluster_right_top = cluster.right_top
	clusters += _get_clusters_right_top(cluster_right_top, n_width-1, n_height-1, update)

	# right
	if cluster.right is None:
		cluster_right = _get_cluster_neighbor(cluster, 5)
		if update: _update_cluster(cluster_right)
	else: cluster_right = cluster.right
	clusters += _get_clusters_right(cluster_right, n_width-1, n_height, update)

	# right bottom
	if cluster.right_bottom is None:
		cluster_right_bottom = _get_cluster_neighbor(cluster, 6)
		if update: _update_cluster(cluster_right_bottom)
	else: cluster_right_bottom = cluster.right_bottom
	clusters += _get_clusters_right_bottom(cluster_right_bottom, n_width-1, n_height-1, update)

	# bottom
	if cluster.bottom is None:
		cluster_bottom = _get_cluster_neighbor(cluster, 7)
		if update: _update_cluster(cluster_bottom)
	else: cluster_bottom = cluster.bottom
	clusters += _get_clusters_bottom(cluster_bottom, n_width, n_height-1, update)

	return clusters

def _update_cluster(cluster):

	if cluster.dirty():

		cluster.update_last = timezone.now()
		cluster.requests = 0
		cluster.updated += 1
		cluster.save()

		work_queue.put(cluster)

def _get_cluster_neighbor(cluster, index):
	return _cluster(
		cluster.geo_lat+cluster_neighbors[index][0],
		cluster.geo_long+cluster_neighbors[index][1])

def _get_clusters_top(cluster, n_width, n_height, update):

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_height <= 0: return clusters

	if cluster.top is not None:
		clusters += _get_clusters_top(cluster.top, n_width, n_height-1, update)
	else: 
		clusters += _get_clusters_top(_get_cluster_neighbor(cluster, 0), n_width, n_height-1, update)

	if cluster.left_top is not None:
		clusters += _get_clusters_left_top(cluster.left_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_top(_get_cluster_neighbor(cluster, 1), n_width-1, n_height-1, update)

	if cluster.right_top is not None:
		clusters += _get_clusters_right_top(cluster.right_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_top(_get_cluster_neighbor(cluster, 4), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_bottom(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_height <= 0: return clusters

	if cluster.bottom is not None:
		clusters += _get_clusters_bottom(cluster.bottom, n_width, n_height-1, update)
	else:
		clusters += _get_clusters_bottom(_get_cluster_neighbor(cluster, 7), n_width, n_height-1, update)

	if cluster.left_bottom is not None:
		clusters += _get_clusters_left_bottom(cluster.left_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_bottom(_get_cluster_neighbor(cluster, 3), n_width-1, n_height-1, update)

	if cluster.right_bottom is not None:
		clusters += _get_clusters_right_bottom(cluster.right_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_bottom(_get_cluster_neighbor(cluster, 6), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_left(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_width <= 0: return clusters

	if cluster.left is not None:
		clusters += _get_clusters_left(cluster.left, n_width-1, n_height, update)
	else:
		clusters += _get_clusters_left(_get_cluster_neighbor(cluster, 2), n_width-1, n_height, update)

	if cluster.left_top is not None:
		clusters += _get_clusters_left_top(cluster.left_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_top(_get_cluster_neighbor(cluster, 1), n_width-1, n_height-1, update)

	if cluster.left_bottom is not None:
		clusters += _get_clusters_left_bottom(cluster.left_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_bottom(_get_cluster_neighbor(cluster, 3), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_right(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_width <= 0: return clusters

	if cluster.right is not None:
		clusters += _get_clusters_right(cluster.right, n_width-1, n_height, update)
	else:
		clusters += _get_clusters_right(_get_cluster_neighbor(cluster, 5), n_width-1, n_height, update)

	if cluster.right_top is not None:
		clusters += _get_clusters_right_top(cluster.right_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_top(_get_cluster_neighbor(cluster, 4), n_width-1, n_height-1, update)

	if cluster.right_bottom is not None:
		clusters += _get_clusters_right_bottom(cluster.right_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_bottom(_get_cluster_neighbor(cluster, 6), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_left_top(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_height <= 0 or n_width <= 0: return clusters

	if cluster.left_top is not None:
		clusters += _get_clusters_left_top(cluster.left_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_top(_get_cluster_neighbor(cluster, 1), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_left_bottom(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]

	if update: _update_cluster(cluster)

	if n_width <= 0 or n_height <= 0: return clusters
	
	n_width  -= 1
	n_height -= 1

	if cluster.left_bottom is not None:
		clusters += _get_clusters_left_bottom(cluster.left_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_left_bottom(_get_cluster_neighbor(cluster, 3), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_right_top(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]
	
	if update: _update_cluster(cluster)

	if n_width <= 0 or n_height <= 0: return clusters

	if cluster.right_top is not None:
		clusters += _get_clusters_right_top(cluster.right_top, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_top(_get_cluster_neighbor(cluster, 4), n_width-1, n_height-1, update)

	return clusters

def _get_clusters_right_bottom(cluster, n_width, n_height, update):

	if cluster is None: return []

	clusters = [ cluster ]
	
	if update: _update_cluster(cluster)

	if n_width <= 0 or n_height <= 0: return clusters

	if cluster.right_bottom is not None:
		clusters += _get_clusters_right_bottom(cluster.right_bottom, n_width-1, n_height-1, update)
	else:
		clusters += _get_clusters_right_bottom(_get_cluster_neighbor(cluster, 6), n_width-1, n_height-1, update)

	return clusters

# -------------------------------------------------------------------

work_queue = queue.Queue()

def _cluster_worker_thread():

	thread_id = threading.get_ident();

	while True:

		created = 0
		updated = 0

		try:

			cluster = work_queue.get(block=True)
			print("Thread[" + str(thread_id) +"] updating " + str(cluster) + " ...")
			created, updated = _cluster_update(cluster)

		except Exception as e:
			traceback.print_exc()
		
def _cluster_update(cluster):

	created, updated = fetcher.fetch_facebook(cluster)
	tmp_created, tmp_updated = fetcher.fetch_yelp(cluster)
	
	created += tmp_created
	updated += tmp_updated
	
	if created > 0 or updated > 0:
		fetcher.calculate_total_score_4_cluster_hotspots(cluster)


	return created, updated

if bool(os.environ.get('start_workers')) is True:
	# start worker threads
	for i in range(0, CLUSTER_WORKER):
		work_thread = threading.Thread(target=_cluster_worker_thread)
		work_thread.start()

