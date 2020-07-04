
function show_details(uuid) 
{
	get_hotspot_content(uuid, function(data){
		var modal = $("#details");
		if(modal !== null) modal.remove();
		$("#wrapper").append(data);
	});
}

function redirect_safe(url)
{
    console.log(url);
    if(url.startsWith("http://"))
    {
	window.open(url,'_blank');
	return;
    }
    if(url.startsWith("https://"))
    {
	window.open(url,'_blank');	
	return;
    }
    window.open("http://" + url,'_blank');	
}

