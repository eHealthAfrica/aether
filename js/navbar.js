var currentScrollY = 0;

var offset = $(".navbar").position().top;
var offset_B = 500;
var height = 60;
document.getElementById("content").addEventListener('scroll', onScroll, false);

navBar = false;
bg = false;
home = false;

if($(document.body).hasClass('home')) {
  home = true;
}

function onScroll() {
  currentScrollY = $(".content").scrollTop();
  if(currentScrollY > offset && navBar==false) {
    navBar = true;
    fixBar();
  } else if(currentScrollY <= offset && navBar==true){
    navBar=false;
    releaseBar();
  }

  if(currentScrollY > offset_B) {
    showTopButton();
  } else if(currentScrollY < offset_B){
    hideTopButton();
  }

  if(home==true) {
    if(currentScrollY > offset_B && bg==false) {
      bg = true;
      hideBg();
    } else if(currentScrollY < offset_B && bg==true){
      bg=false;
      showBg();
    }
  }
}

function fixBar() {
  $(".navbar").addClass('fixed');
}

function releaseBar() {
  $(".navbar").removeClass('fixed');
}

function showTopButton() {
  $(".top").addClass('active');
}

function hideTopButton() {
  $(".top").removeClass('active');
}

function hideBg() {
  $(".background").addClass('hidden');
  $(".nav-item__about").addClass('active');
  $(".anchor-nav").addClass('active');
}

function showBg() {
  $(".background").removeClass('hidden');
  $(".nav-item__about").removeClass('active');
  $(".anchor-nav").removeClass('active');
}


$('a[href^=#]').on('click', function(e){
    var href = $(this).attr('href');
    var position = $(".content").scrollTop() + $(href).offset().top - height;
        e.preventDefault();
    $(".content").animate({
      scrollTop:position
    },'slow');

});
