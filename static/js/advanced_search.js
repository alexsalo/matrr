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
	for(var i= 0; i<inputs.length; i++){
		if (inputs[i].type == 'checkbox' && inputs[i].checked)
			checkboxes.push(inputs[i]);
	}
	return checkboxes;
}

function getMonkeyTRElements() {
	var all_trs = document.getElementsByTagName("tr");
	var monkey_trs = [];
	for(var i= 0; i<all_trs.length; i++){
		if (all_trs[i].id.indexOf('monkey_') != -1 )
			monkey_trs.push(all_trs[i]);
	}
	return monkey_trs;
}

function collectTRToShowOrHide(show_or_hide) {
	var monkey_trs = getMonkeyTRElements();
	var boxes = getSelectedCheckboxes();
	var sexes = [];
	var species = [];
	var proteins = [];
	for(var cb=0; cb<boxes.length; cb++){
		if(boxes[cb].name == 'sex')
			sexes.push("_".concat(boxes[cb].value));
		if(boxes[cb].name == 'species')
			species.push("_".concat(boxes[cb].value));
		if(boxes[cb].name == 'proteins')
			proteins.push("_".concat(boxes[cb].value));
	}

	var toShow = [];
	var toHide = [];
	var proteins_selected = proteins.length != 0;
	for(var tr= 0; tr< monkey_trs.length; tr++){
		var mky = monkey_trs[tr];
		var display_sex = false;
		var display_species = false;
		var display_protein = false;
		if(sexes.length > 0)
			for(var s=0; s<sexes.length; s++){
				if(mky.className.indexOf(sexes[s]) != -1)
					display_sex = true;
			}
		if(species.length > 0)
			for(var i=0; i<species.length; i++){
				if(mky.className.indexOf(species[i]) != -1)
					if(display_sex){
						display_species = true;
					}
			}
		if(proteins.length > 0)

			for(var p=0; p<proteins.length; p++){
				if(mky.className.indexOf(proteins[p]) != -1)
					display_protein = true;
			}

		var _show = false;
		if(display_sex && display_species)
			_show = true;
		if (proteins_selected)
			_show = display_protein && _show;

		if(_show)
			toShow.push(mky.id);
		else
			toHide.push(mky.id);
	}
	if(show_or_hide == 'show')
		return toShow;
	else
		return toHide;
}

function updateTRToShow(){
	var toShow = collectTRToShowOrHide('show');
	var toHide = collectTRToShowOrHide('hide');
	for(var i=0; i<toShow.length; i++){
		showElementByID(toShow[i]);
	}
	for(var j=0; j<toHide.length; j++){
		hideElementByID(toHide[j]);
	}
}