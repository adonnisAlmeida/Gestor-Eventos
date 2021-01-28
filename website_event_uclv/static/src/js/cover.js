
$(window).scroll(function()
	{
		var scroll = $(window).scrollTop()	
		var cover = $('.o_record_cover_component.o_record_cover_filter')
		var alpha = 0.5 + (scroll/cover.height())	
		cover.css("opacity", alpha)		
		if(scroll>60)
		{
			$('.navbar.navbar-expand-md').removeClass("bg-light").removeClass("navbar-light").addClass("navbar-dark").addClass("bg-dark");
			
		}
		else
		{
			$('.navbar.navbar-expand-md').removeClass("bg-dark").removeClass("navbar-dark").addClass("navbar-light").addClass("bg-light");		
		}
		
	});