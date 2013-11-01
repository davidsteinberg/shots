$(document).ready(function(){
	function get_random_rgb() {
		red = Math.floor(Math.random()*256);
		green = Math.floor(Math.random()*256);
		blue = Math.floor(Math.random()*256);
		return "rgb(" + red + "," + green + "," + blue +")";
	}

	$("#brand_name").mouseenter(function(){
		$(this).css("color",get_random_rgb());
	}).mouseleave(function(){
		$(this).css("color","black")
	});
});
