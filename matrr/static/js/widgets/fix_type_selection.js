
function updateSelection(elementID) {
 var selection = document.getElementById(elementID + '_selection');
 var item = document.getElementById(elementID);
 if (selection.value == "other") {
  item.className='';
  item.value='';
 }else{
  item.className='hidden';
  item.value=selection.value;
 }
}