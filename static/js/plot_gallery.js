		$(document).ready(function(){
			//Examples of how to assign the ColorBox event to elements
			$("a[rel='plot_gallery']").colorbox({opacity:0.5, maxHeight:"75%"});
				
			//Example of preserving a JavaScript event for inline calls.
			$("#click").click(function(){ 
				$('#click').css({"background-color":"#f00", "color":"#fff", "cursor":"inherit"}).text("Open this window again and this message will still be here.");
				return false;
			});
		});