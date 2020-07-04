// Bind event listeners
$(document).ready(function(){
	$("#filter-all").click(function(e) {
		e.preventDefault();
		toggleFilter();
	});

	$("#filter-hotels").click(function(e) {
		e.preventDefault();
		toggleFilter(1);
	});

	$("#filter-food").click(function(e) {
		e.preventDefault();
		toggleFilter(2);
	});

	$("#filter-entertainment").click(function(e) {
		e.preventDefault();
		toggleFilter(3);
	});

	$("#filter-shops").click(function(e) {
		e.preventDefault();
		toggleFilter(4);
	});

	$("#filter-travel").click(function(e) {
		e.preventDefault();
		toggleFilter(5);
	});

	$("#filter-unknown").click(function(e) {
		e.preventDefault();
		toggleFilter(0);
	});
});

function remove(array, index) {
	if (index < 0)
		return array;
	return array.slice(0, index).concat(array.slice(index + 1));
}

function toggleFilter(f) {
	var s = globalFilter.split(",");
	s = remove(s, s.indexOf(""));

	if (f != null) {
		tmp = f.toString();
		// Toggle given filter
		if (s.indexOf(tmp) < 0) {
			s.push(tmp);
		} else {
			s = remove(s, s.indexOf(tmp));
		}

		// Check if all filter are active
		if (s.length == 5)
			s = [];
	} else {
		s = [];
	}
	setFilterAndRedrawMap(s.join(","));
	updateFilterLabels();
}

function setFilterAndRedrawMap(filter="") {
	globalFilter = filter;
	updateSources(globalCache);
}

function updateFilterLabels() {
	if (globalFilter == "") {
		($(".all-bg").removeClass("disabled"));
		($(".food-bg").removeClass("disabled"));
		($(".hotel-bg").removeClass("disabled"));
		($(".entertainment-bg").removeClass("disabled"));
		($(".shop-bg").removeClass("disabled"));
		($(".travel-bg").removeClass("disabled"));
		($(".unknown-bg").removeClass("disabled"));
	} else {
		s = globalFilter.split(",");
		(s.indexOf("") < 0)?($(".all-bg").addClass("disabled")):($(".all-bg").removeClass("disabled"));
		(s.indexOf("0") < 0)?($(".unknown-bg").addClass("disabled")):($(".unknown-bg").removeClass("disabled"));
		(s.indexOf("2") < 0)?($(".food-bg").addClass("disabled")):($(".food-bg").removeClass("disabled"));
		(s.indexOf("1") < 0)?($(".hotel-bg").addClass("disabled")):($(".hotel-bg").removeClass("disabled"));
		(s.indexOf("3") < 0)?($(".entertainment-bg").addClass("disabled")):($(".entertainment-bg").removeClass("disabled"));
		(s.indexOf("4") < 0)?($(".shop-bg").addClass("disabled")):($(".shop-bg").removeClass("disabled"));
		(s.indexOf("5") < 0)?($(".travel-bg").addClass("disabled")):($(".travel-bg").removeClass("disabled"));
	}
}

function drawFilter(f) {
	var s = f.split(",");

	var f = [];
	s.forEach(function(element)
	{
		if(element == "unknown") {
			f.push(0)
		} else if(element == "hotel") {
			f.push(1);
		} else if(element == "food") {
			f.push(2);
		} else if(element == "arts") {
			f.push(3)
		} else if(element == "shop") {
			f.push(4)
		} else if(element == "travel") {
			f.push(5)
		} else {
			f.push(element);
		}
	});

	setFilterAndRedrawMap(f.join(","));
}
