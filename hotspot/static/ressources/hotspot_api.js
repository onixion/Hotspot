
function get_hotspots(geo_lat, geo_long, filter, callback)
{
	$.ajax({
		url:"/api/hotspots/",
		method:"GET",
		data:{"geo_lat":geo_lat,"geo_long":geo_long,"filter":filter},
		success:function(data) { callback(data); }
	});
}

function get_hotspot(uuid, callback)
{
	$.ajax({
		url:"/api/hotspot/",
		method:"GET",
		data:{"uuid":uuid},
		success:function(data) { callback(data); }
	});
}

function get_hotspot_content(uuid, callback)
{
	console.log(uuid);
	$.ajax({
		url:"/api/hotspot/content/",
		method:"GET",
		data:{"uuid":uuid},
		success:function(data) { callback(data); }
	});
}

function draw_hotspots(geo_lat, geo_long, filter)
{
	show_spinner();

	get_hotspots(geo_lat, geo_long, filter, function(data){

		// try again after 10 seconds
		if(data.features.length == 0) {
			setTimeout(function(){
				draw_hotspots(geo_lat, geo_long, filter);
			}, 10000);
			return;
		}

		updateSources(data);
		hide_spinner();
	});
}

function get_clusters(callback)
{
	$.ajax({
		url:"/api/clusters/",
		method:"GET",
		success:function(data) { callback(data); }
	});
}

function draw_clusters()
{
	get_clusters(function(data){

		if(map.getLayer("clusters-points") != undefined)
			map.removeLayer("clusters-points");

		if(map.getSource("clusters") != undefined)
			map.removeSource("clusters");

		map.addSource("clusters", {
			"type": "geojson",
			"data": data,
		});

		map.addLayer({
			"id": "clusters-points",
			"type": "circle",
			"source": "clusters",
			"paint": {
				"circle-radius": {
					"base": 1,
					"stops": [[12, 5], [22, 10]]
				},
			}
		});
	});
}

function get_clusters_grid(callback)
{
	$.ajax({
		url:"/api/clusters/grid/",
		method:"GET",
		success:function(data) { callback(data); }
	});
}

function draw_clusters_grid()
{
	get_clusters_grid(function(data){

		if(map.getLayer("clusters-grid-layer") != undefined)
			map.removeLayer("clusters-grid-layer");

		if(map.getSource("clusters-grid-id") != undefined)
			map.removeSource("clusters-grid-id");

		map.addSource("clusters-grid-id", {
			"type": "geojson",
			"data": data,
		});

		map.addLayer({
			"id": "clusters-grid-layer",
			"type": "line",
			"source": "clusters-grid-id",
			"paint": {
				"line-color": "#888",
				"line-width": 0.2,
			}
		});
	});
}

function get_some_hotspots()
{
	get_hotspots(47.1822454,10.6240727,"",function(){});
	get_hotspots(47.2773651,10.9783818,"",function(){});
	get_hotspots(47.2778309,10.9062840,"",function(){});
	get_hotspots(47.2871471,11.1781956,"",function(){});
	get_hotspots(47.2568635,11.2805058,"",function(){});
	get_hotspots(47.3388222,11.6924931,"",function(){});
	get_hotspots(47.4930802,12.0550419,"",function(){});
}

function get_hotspots_area(geo_lat, geo_long, geo_lat2, geo_long2, filter, callback)
{
	$.ajax({
		url:"/api/hotspots/area/",
		method:"GET",
		data:
		{
			"geo_lat":   geo_lat,
			"geo_long":  geo_long,
			"geo_lat2":  geo_lat2,
			"geo_long2": geo_long2,
			"filter":    filter
		},
		success:function(data) { callback(data); }
	});
}

var locked = false;

function draw_hotspots_area(lat, long, lat2, long2, filter)
{
	if(locked) return;
	locked = true;

	setTimeout(function(){locked=false},2000);

	show_spinner();

	get_hotspots_area(lat, long, lat2, long2, filter, function(data) {
		updateSources(data);
		hide_spinner();
	});
}
