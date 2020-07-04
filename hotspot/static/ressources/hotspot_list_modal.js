function tableCreate(elements) {
	var categories = {
		0: "Unknown",
		1: "Hotels",
		2: "Food & Restaurants",
		3: "Entertainment & Arts",
		4: "Shops",
		5: "Travel"
	};

	var tbl = document.getElementById('hotspot-list-table');

	// Delete old table header and tbody
	if(document.getElementById("hotspot-list-table-header")) {
		document.getElementById("hotspot-list-table-header").remove();
	}

	if(document.getElementById("hotspot-list-table-body")) {
		document.getElementById("hotspot-list-table-body").remove();
	}

	// Create table header content
	var thd = tbl.createTHead();
	var hdRow = thd.insertRow(0);

	thd.setAttribute("id", "hotspot-list-table-header");

	hdRow.insertCell(0).innerHTML = "<b>Name</b>";
	hdRow.insertCell(1).innerHTML = "<b>Score</b>";
	hdRow.insertCell(2).innerHTML = "<b>Category</b>";

	// Create table body content
	var tbdy = tbl.appendChild(document.createElement('tbody'));
	tbdy.setAttribute("id", "hotspot-list-table-body");

	// Remove duplicates
	for (var i = 0; i < elements.length; i++) {
		for (var j = elements.length - 1; j > i; j--) {
			if (elements[i].properties.uuid == elements[j].properties.uuid)
				elements = remove(elements, j);
		}
	}

	elements.forEach(function(e) {
		var row = tbdy.insertRow(-1);

		var cellName = row.insertCell(0);
		var cellScore = row.insertCell(1);
		var cellCategory = row.insertCell(2);

		cellName.innerHTML = e.properties.name;
		cellScore.innerHTML = e.properties.score;
		cellCategory.innerHTML = categories[e.properties.category];

		// Add fly to hotspot on row click
		row.addEventListener('click', function () {
			$('#hotspot-list-modal').modal('hide');
			map.flyTo({center: [e.geometry.coordinates[0], e.geometry.coordinates[1]], zoom: 18});
			openMapPopUp(e);
		});
	});
}

$("#hotspot-list-modal").on('shown.bs.modal', function(){
	$("#wrapper").toggleClass("toggled");
	tableCreate(map.queryRenderedFeatures({ layers: ['hotspots-points'] }));
});
