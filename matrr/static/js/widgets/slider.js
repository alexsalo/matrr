function slider_behavior() {
    $('.slider').each(function (index) {
        var input_id = '#id_' + this.id.replace('_slider', '');
        var slider_val = '#' + this.id + '_value';
        var slider_unit = '#' + this.id + '_unit';
        $('#'+this.id).slider({
            max:+$(input_id).attr('max'),
            min:+$(input_id).attr('min'),
            step:+$(input_id).attr('step'),
            value:+$(input_id).val(),
            slide: function(event, ui) {
                $(slider_val).html(ui.value);
                $(input_id).val(ui.value);
            }
        })
        $(slider_unit).html($(input_id).attr('unit'));
    }); 
}       

add_behavior(slider_behavior);
