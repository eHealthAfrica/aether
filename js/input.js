$('.input input').keyup(function (e) {
    if($(this).val().length) {
      $(this).closest('.input').addClass('active');
    } else {
      $(this).closest('.input').removeClass('active');
    };
    e.preventDefault();
});

$('.input').on('click', function(e){
	$(this).addClass('active');
    e.preventDefault();
});


