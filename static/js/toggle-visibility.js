/**
 * Created by PyCharm.
 * User: soltau
 * Date: 5/10/11
 * Time: 10:05 AM
 * To change this template use File | Settings | File Templates.
 */

function toggle_visibility(divID) {
 var item = document.getElementById(divID);
 if (item) {
  item.className=(item.className=='hidden')?'':'hidden';
 }
}