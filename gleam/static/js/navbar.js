(function($){
	$(document).ready(function(){
		// Fixed header
		//-----------------------------------------------
		$(window).scroll(function() {
			if (($(".header.fixed").length > 0)) {
				if(($(this).scrollTop() > 0) && ($(window).width() > 767)) {
					$("#top-navbar").addClass("navbar-fixed-top");
				} else {
					$("#top-navbar").removeClass("navbar-fixed-top");
				}
			};
		});

		$(window).load(function() {
			if (($(".header.fixed").length > 0)) {
				if(($(this).scrollTop() > 0) && ($(window).width() > 767)) {
					$("#top-navbar").addClass("navbar-fixed-top");
				} else {
					$("#top-navbar").removeClass("navbar-fixed-top");
				}
			};
		});
	}); // End document ready
})(this.jQuery);