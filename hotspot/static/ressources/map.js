
// Used for client site filtering
var globalCache = undefined;
var globalFilter = "";

var austria_bound = [
	[9.2947270,46.4503946],
	[17.5125004,49.1720520],
]

function redrawMap() {

	var bounds = map.getBounds();

	var southeast = bounds.getSouthEast();
	var northwest = bounds.getNorthWest();

	draw_hotspots_area(southeast.lat, southeast.lng, northwest.lat, northwest.lng, "");
}

// Use this function to update the source of the map.
// The map gets redrawn automatically.
function updateSources(data) {
	var filter = globalFilter.split(",");
	var filteredData = {features: [], type: "FeatureCollection"};

	// Chache received data before filtering
	globalCache = data;

	if (filter[0] != "") {
		for (var i = 0; i < data.features.length; i++) {
			var currentFeature = data.features[i];
			if (filter.indexOf(currentFeature.properties.category.toString()) > -1) {
				filteredData.features.push(currentFeature);
			}
		}
	} else {
		filteredData = data;
	}

	map.getSource("hotspots-heat").setData(filteredData);
	map.getSource("hotspots-points").setData(filteredData);
}

function openMapPopUp(e) {
	var properties = undefined;

	if (e.features != undefined)
		properties = e.features[0].properties;
	else if (e.properties != undefined)
		properties = e.properties;

	html = []
	html.push("<div class='container' style='width:auto;'>");

	if(properties.image !== "null" && properties.image !== "None")
	{
		html.push("<div class='row'>");

		// image
		html.push("<div class='col-xs-3'>");
		html.push("<img class='img-fluid' src='" + properties.image + "' alt='Logo'>");
		html.push("</div>");

		// name
		html.push("<div class='col-xs-9' class='text-center'>");
		html.push("<h4><b>" + properties.name + "</b></h4>");
		html.push("</div>");

		html.push("</div>");
	}
	else
	{
		html.push("<div class='row'>");

		// name
		html.push("<div class='col text-center' style='padding:5px;'>");
		html.push("<h4><b>" + properties.name + "</b></h4>");
		html.push("</div>");

		html.push("</div>");
	}

	html.push("<div class='row'>");

	// score
	html.push("<div class='col-xs-12'>");
	html.push("<h6><b>Score: " + properties.score + "</b></h6>")
	html.push("</div>");

	// plausibility
	//html.push("<div class='col-xs-6'>");
	//html.push("<h6><b>plausibility: " + properties.plausibility + "</b></h6>")
	//html.push("</div>");

	html.push("</div>");

	if(properties.url !== "null" && properties.url !== "None")
        {
		html.push("<div class='row'>");
		html.push("<div class='col text-center'>");
		html.push("<div class='btn-group'>");

		// homepage
		html.push("<button class='btn btn-primary' onclick=\"redirect_safe('" +
			properties.url + "');\">Homepage</button>");

		// details
		html.push("<button class='btn btn-primary' onclick=\"show_details('");
		html.push(properties.uuid);
		html.push("');\">Details</button>");

		html.push("</div>");
		html.push("</div>");
		html.push("</div>");
	}
	else
	{
	    html.push("<div class='row'>");
	    html.push("<div class='col text-center'>");
	    // details
	    html.push("<button class='btn btn-primary' onclick=\"show_details('");
	    html.push(properties.uuid);
	    html.push("');\">Details</button>");
	    
	    html.push("</div>");
	    html.push("</div>");	    
	}

	html.push("</div>");


	if (e.features != undefined) {
		new mapboxgl.Popup()
		.setLngLat(e.features[0].geometry.coordinates)
		.setHTML(html.join(""))
		.addTo(map);
	} else if (e.geometry != undefined) {
		new mapboxgl.Popup()
		.setLngLat(e.geometry.coordinates)
		.setHTML(html.join(""))
		.addTo(map);
	}


	$(".mapboxgl-popup-close-button").remove();
}

mapboxgl.accessToken = 'pk.eyJ1Ijoic2NoYWZmZW5yYXRoIiwiYSI6ImNqOTg1dTh0MzBlbmczM2xzYnF6Y2h3ZGkifQ.FsrNjCxfz9aijrIL6YZL0Q';
map = new mapboxgl.Map({
	container: 'map',
	style: 'mapbox://styles/mapbox/bright-v9',
	center: [11.404, 47.27],
	zoom: 1,
	maxBounds: austria_bound,
});

// Add GeolocateControl button to map
map.addControl(new mapboxgl.GeolocateControl({
	positionOptions: {
		enableHighAccuracy: true
	},
	trackUserLocation: true
}));

map.on('load', function(e) {
	map.addSource('hotspots-heat', {
		"type": "geojson",
		"data": false,
	});

	// Mapbox needs different sources for heatmap and points
	// otherwise an typeerror occurs.
	map.addSource('hotspots-points', {
		"type": "geojson",
		"data": false,
	});

	map.addLayer({
		"id": "hotspots-heat",
		"type": "heatmap",
		"source": "hotspots-heat",
		"maxzoom": 22,
		"paint": {
			"heatmap-weight": {
				"property": "score",
				"type": "exponential",
				"stops": [
					[0, 0.0],
					[50, 1.0],
				]
			},
			"heatmap-intensity": {
				"type": "exponential",
				"stops": [
					[0, 1.0],
					[22, 1.0]
				]
			},
			"heatmap-color": {
				"stops": [
					[0.0,  "rgba(255, 255, 0, 0)"],
					[0.5,  "rgb(255, 130, 0)"],
					[0.75, "rgb(255,  70, 0)"],
					[1,    "rgb(255,   0, 0)"],
				]
			},
			"heatmap-radius": {
				"type": "exponential",
				"stops": [
					[0,  10],
					[13, 50],
					[18, 400],
					[22, 500],
				]
			},
			'heatmap-opacity': {
				"stops": [
					[0,  0.3],
					[22, 0.8],
				]
			},
		}
	});

	map.addLayer({
		"id": "hotspots-points",
		"type": "circle",
		"source": "hotspots-points",
		//"minzoom": 15,
		"paint": {
			// Size circle raidus by magnitude and zoom level
			"circle-radius": {
				"property" : "score",
				"type": "exponential",
				"stops": [
					[{ zoom: 10, value: 100},   5],
					[{ zoom: 22, value: 100 }, 14],
				]
			},
			// Color circle by category
			"circle-color": {
				"property": "category",
				"stops": [ 
					[0, "rgba(33,102,172,0)"],
					[1, "#ff9900"],
					[2, "#00ff00"],
					[3, "#ffff00"],
					[4, "#cc0066"],
					[5, "#0000ff"],
				]
			},
			// Transition from heatmap to circle layer by zoom level
			"circle-opacity": {
				"stops": [
					[12, 0],
					[15, 1],
				]
			}
		}
	});

	redrawMap();
});

map.on('move', redrawMap);

// When a click event occurs on a feature in the places layer, open a popup at the
// location of the feature, with description HTML from its properties.
map.on('click', 'hotspots-points', openMapPopUp);

// Change the cursor to a pointer when the mouse is over the places layer.
map.on('mouseenter', 'hotspots-points', function () {
	map.getCanvas().style.cursor = 'pointer';
});

// Change it back to a pointer when it leaves.
map.on('mouseleave', 'hotspots-points', function () {
	map.getCanvas().style.cursor = '';
});
