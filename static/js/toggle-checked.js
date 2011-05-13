function toggle_checked(source, other) {
  var checkboxes = document.getElementsByName(other);
  for(var i in checkboxes)
    checkboxes[i].checked = source.checked;
}

function check_toggler(source, other) {
  var checkboxes = document.getElementsByName(other);
  var total = 0;
  var checked = 0;
  for( i=0; i < checkboxes.length;++i){
    total += 1;
    if(checkboxes[i].checked){
      checked += 1;
    }
  }
  if(total == checked){
    source.checked = true;
  }else{
    source.checked = false;
  }
}