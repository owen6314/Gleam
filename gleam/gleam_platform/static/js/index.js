(function($){
	$(document).ready(function(){
		// Fixed header
		//-----------------------------------------------
		$(window).scroll(function() {
			if (($(".header.fixed").length > 0)) {
				if(($(this).scrollTop() > 0) && ($(window).width() > 767)) {
					$("body").addClass("fixed-header-on");
				} else {
					$("body").removeClass("fixed-header-on");
				}
			};
		});

		$(window).load(function() {
			if (($(".header.fixed").length > 0)) {
				if(($(this).scrollTop() > 0) && ($(window).width() > 767)) {
					$("body").addClass("fixed-header-on");
				} else {
					$("body").removeClass("fixed-header-on");
				}
			};
		});
	}); // End document ready
})(this.jQuery);