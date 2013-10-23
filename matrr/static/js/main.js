var behaviors = new Array();
function add_behavior(functor)
{           
    behaviors.push(functor);
}               
                
$(document).ready(function() {
    // Add behaviors specified by widgets
    for (var i=behaviors.length-1; i>=0; --i) {
        behaviors[i]();
    }   
});
