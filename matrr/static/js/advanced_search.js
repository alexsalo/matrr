function showElementByID(id) {
	var element = document.getElementById(id);
	if (element.className.indexOf('hidden') != -1) {
		element.className = element.className.replace(" hidden", '');
	}
}

function hideElementByID(id) {
	var element = document.getElementById(id);
	if (element.className.indexOf('hidden') == -1) {
		element.className += " hidden";
	}
}

function getSelectedCheckboxes() {
	var inputs = document.getElementsByTagName('input');
	var checkboxes = [];
	for (var i = 0; i < inputs.length; i++) {
		if (inputs[i].type == 'checkbox' && inputs[i].checked)
			checkboxes.push(inputs[i]);
	}
	return checkboxes;
}

function getMonkeyTRElements() {
	var all_trs = document.getElementsByTagName("tr");
	var monkey_trs = [];
	for (var i = 0; i < all_trs.length; i++) {
		if (all_trs[i].id.indexOf('monkey_') != -1)
			monkey_trs.push(all_trs[i]);
	}
	return monkey_trs;
}

function collectTRToShowOrHide(show_or_hide) {
	var monkey_trs = getMonkeyTRElements();
	var boxes = getSelectedCheckboxes();
	var control = [];
	var cohort = [];
	var sexes = [];
	var species = [];
	var proteins = [];
	var hormones = [];
    var bone_density = [];
	for (var cb = 0; cb < boxes.length; cb++) {
		if (boxes[cb].name == 'control')
			control.push("_".concat(boxes[cb].value));
		if (boxes[cb].name == 'cohort')
			cohort.push("_".concat(boxes[cb].value));
		if (boxes[cb].name == 'sex')
			sexes.push("_".concat(boxes[cb].value));
		if (boxes[cb].name == 'species')
			species.push("_".concat(boxes[cb].value));
		if (boxes[cb].name == 'proteins')
			proteins.push("_".concat(boxes[cb].value));
		if (boxes[cb].name == 'hormones')
			hormones.push("_".concat(boxes[cb].value));
        if (boxes[cb].name == 'bone_density')
			bone_density.push("_".concat(boxes[cb].value));
	}

	var toShow = [];
	var toHide = [];
	var proteins_selected = proteins.length != 0;
	var hormones_selected = proteins.length != 0;
	var control_selected = control.length != 0;
	var cohort_selected = cohort.length != 0;
    var bone_density_selected = bone_density.length != 0;
	for (var tr = 0; tr < monkey_trs.length; tr++) {
		var mky = monkey_trs[tr];
		var display_sex = false;
		var display_species = false;
		var display_protein = false;
		var display_hormone = false;
		var display_control = false;
		var display_cohort = false;
        var display_bone_density = false;
		if (sexes.length > 0)
			for (var s = 0; s < sexes.length; s++) {
				if (mky.className.indexOf(sexes[s]) != -1)
					display_sex = true;
			}
		if (species.length > 0)
			for (var i = 0; i < species.length; i++) {
				if (mky.className.indexOf(species[i]) != -1)
					if (display_sex) {
						display_species = true;
					}
			}
		if (proteins.length > 0)
			for (var p = 0; p < proteins.length; p++) {
				if (mky.className.indexOf(proteins[p]) != -1)
					display_protein = true;
			}
		if (hormones.length > 0)
			for (var p = 0; p < hormones.length; p++) {
				if (mky.className.indexOf(hormones[p]) != -1)
					display_hormone = true;
			}
		if (cohort.length > 0)
			for (var p = 0; p < cohort.length; p++) {
				if (mky.className.indexOf(cohort[p]) != -1)
					display_cohort = true;
			}
		if (control.length > 0)
			for (var p = 0; p < control.length; p++) {
				if (mky.className.indexOf(control[p]) != -1)
					display_control = true;
			}
        if (bone_density.length > 0)
			for (var p = 0; p < bone_density.length; p++) {
				if (mky.className.indexOf(bone_density[p]) != -1)
					display_bone_density = true;
			}

		var _show = false;
		if (display_sex && display_species) {
			if (cohort_selected) {
				if (display_cohort)
					_show = true;
			}
			else
				_show = true;
		}
		if (proteins_selected)
			_show = display_protein && _show;
        if (bone_density_selected)
			_show = display_bone_density && _show;
		if (hormones_selected)
			_show = display_hormone && _show;
		if (control_selected)
			_show = display_control && _show;

		if (_show)
			toShow.push(mky.id);
		else
			toHide.push(mky.id);
	}
	if (show_or_hide == 'show')
		return toShow;
	else
		return toHide;
}

function updateTRToShow() {
	var toShow = collectTRToShowOrHide('show');
	var toHide = collectTRToShowOrHide('hide');
	for (var i = 0; i < toShow.length; i++) {
		showElementByID(toShow[i]);
	}
	for (var j = 0; j < toHide.length; j++) {
		hideElementByID(toHide[j]);
	}
}

function toggle_named_checkboxes(source) {
	checkboxes = document.getElementsByName(source.name);
	for (var cb = 0; cb < checkboxes.length; cb++)
		checkboxes[cb].checked = source.checked;
	updateTRToShow();
	post_adv_form();
}

function parse_json_response(response){
	var json_string = response.responseText;
	var json = $.parseJSON(json_string);
	var show_ids = json['show_ids'];
	var hide_ids = json['hide_ids'];
	for (var i = 0; i < show_ids.length; i++) {
		showElementByID('monkey_' + show_ids[i]);
	}
	for (var i = 0; i < hide_ids.length; i++) {
		hideElementByID('monkey_' + hide_ids[i]);
	}
}