$(document).ready(function(){
  $('.sidenav').sidenav({edge: "right"});
  $('.slider').slider( {
    'indicators': false,
    'height': 500,
  }
  );
  $('.modal').modal();
  $('.datepicker').datepicker({
      yearRange: 1,

  });
});
