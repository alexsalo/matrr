// -jf

// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
function draw_chord_plot(cohort_pk, matrix, name_color) {
// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
	var width = 500,
			height = 500,
			outerRadius = Math.min(width, height) / 2 - 10,
			innerRadius = outerRadius - 24;

	var formatPercent = d3.format(".1%");

	var arc = d3.svg.arc()
			.innerRadius(innerRadius)
			.outerRadius(outerRadius);

	var layout = d3.layout.chord()
			.padding(.04)
			.sortSubgroups(d3.descending)
			.sortChords(d3.ascending);

	var path = d3.svg.chord()
			.radius(innerRadius);

	var svg = d3.select("#coh_" + cohort_pk).append("svg")
			.attr("width", width)
			.attr("height", height)
			.attr("class", "circle")
			.append("g")
			.attr("id", "coh_" + cohort_pk + "_circle")
			.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

	svg.append("circle")
			.attr("r", outerRadius);

	// Compute the chord layout.
	layout.matrix(matrix);

	// Add a group per neighborhood.
	var group = svg.selectAll(".group")
			.data(layout.groups)
			.enter().append("g")
			.attr("class", "group")
			.on("mouseover", mouseover);

	// Add a mouseover title.
	group.append("title").text(function (d, i) {
		return name_color[i].name + ": " + formatPercent(d.value) + " of origins";
	});

	// Add the group arc.
	var groupPath = group.append("path")
			.attr("id", function (d, i) {
					  return cohort_pk + "group" + i;
				  })
			.attr("d", arc)
			.style("fill", function (d, i) {
					   return name_color[i].color;
				   });

	// Add a text label.
	var groupText = group.append("text")
			.attr("x", 6)
			.attr("dy", 15);

	groupText.append("textPath")
			.attr("xlink:href", function (d, i) {
					  return "#" + cohort_pk + "group" + i;
				  })
			.text(function (d, i) {
					  return name_color[i].name;
				  });

	// Remove the labels that don't fit. :(
	groupText.filter(function (d, i) {
		return groupPath[0][i].getTotalLength() / 2 - 16 < this.getComputedTextLength();
	})
			.remove();

	// Add the chords.
	var chord = svg.selectAll(".chord")
			.data(layout.chords)
			.enter().append("path")
			.attr("class", "chord")
			.style("fill", function (d) {
					   return name_color[d.source.index].color;
				   })
			.attr("d", path);

	// Add an elaborate mouseover title for each chord.
	chord.append("title").text(function (d) {
		return name_color[d.source.index].name
				+ " → " + name_color[d.target.index].name
				+ ": " + formatPercent(d.source.value)
				+ "\n" + name_color[d.target.index].name
				+ " → " + name_color[d.source.index].name
				+ ": " + formatPercent(d.target.value);
	});

	function mouseover(d, i) {
		chord.classed("fade", function (p) {
			return p.source.index != i
					&& p.target.index != i;
		});
	}
}


// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
function draw_adjacency_matrix(cohort_pk) {
// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
	var margin = {top:80, right:0, bottom:10, left:160},
			width = 500,
			height = 500;

	var x = d3.scale.ordinal().rangeBands([0, width]),
			c = {4: '#FF0000', 3: '#FF6600', 2: '#008000', 1: '#0052CC'};

	var svg = d3.select("#coh_" + cohort_pk).append("svg")
			.attr("width", width + margin.left + margin.right)
			.attr("height", height + margin.top + margin.bottom)
			.style("margin-left", -margin.left + "px")
			.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json("/static/js/" + cohort_pk + ".RAN.json", function (cooccurency_matrix) {
		var matrix = [],
				nodes = cooccurency_matrix.nodes,
				nodes_length = nodes.length;

		// Compute index per node.
		nodes.forEach(function (node, i) {
			node.index = i;
			node.count = 0;
			matrix[i] = d3.range(nodes_length).map(function (j) {
				return {x:j, y:i, z:0};
			});
		});

		// Convert links to matrix; count character occurrences.
		var min_cbt_count = 1000000;
		var max_cbt_count = 0;
		cooccurency_matrix.links.forEach(function (link) {
			matrix[link.source][link.target].z += link.cbt_count;
			matrix[link.target][link.source].z += link.cbt_count;
			matrix[link.source][link.source].z += link.cbt_count;
			matrix[link.target][link.target].z += link.cbt_count;
			nodes[link.source].count += link.cbt_count;
			nodes[link.target].count += link.cbt_count;
			min_cbt_count = Math.min(link.cbt_count, min_cbt_count);
			max_cbt_count = Math.max(link.cbt_count, max_cbt_count);
		});
		var z = d3.scale.linear().domain([min_cbt_count, max_cbt_count]).clamp(true);

		// Precompute the orders.
		var orders = {
			monkey:d3.range(nodes_length).sort(function (a, b) {
				return d3.ascending(nodes[a].monkey, nodes[b].monkey);
			}),
			count:d3.range(nodes_length).sort(function (a, b) {
				return nodes[b].count - nodes[a].count;
			}),
			group:d3.range(nodes_length).sort(function (a, b) {
				var group_diff = nodes[b].group - nodes[a].group;
				if (group_diff == 0)
					return nodes[b].count - nodes[a].count;
				else
					return group_diff

			})
		};

		// The default sort order.
		x.domain(orders.monkey);

		svg.append("rect")
				.attr("class", "background")
				.attr("width", width)
				.attr("height", height);

		var row = svg.selectAll(".row")
				.data(matrix)
				.enter().append("g")
				.attr("class", "row")
				.attr("transform", function (d, i) {
						  return "translate(0," + x(i) + ")";
					  })
				.each(row);

		row.append("line")
				.attr("x2", width);

		row.append("text")
				.attr("x", -6)
				.attr("y", x.rangeBand() / 2)
				.attr("dy", ".32em")
				.attr("text-anchor", "end")
				.text(function (d, i) {
						  return nodes[i].monkey;
					  });

		var column = svg.selectAll(".column")
				.data(matrix)
				.enter().append("g")
				.attr("class", "column")
				.attr("transform", function (d, i) {
						  return "translate(" + x(i) + ")rotate(-90)";
					  });

		column.append("line")
				.attr("x1", -width);

		column.append("text")
				.attr("x", 6)
				.attr("y", x.rangeBand() / 2)
				.attr("dy", ".32em")
				.attr("text-anchor", "start")
				.text(function (d, i) {
						  return nodes[i].monkey;
					  });

		function row(row) {
			var cell = d3.select(this).selectAll(".cell")
					.data(row.filter(function (d) {
								return d.z;
							}))
					.enter().append("rect")
					.attr("class", "cell")
					.attr("x", function (d) {
							  return x(d.x);
						  })
					.attr("width", x.rangeBand())
					.attr("height", x.rangeBand())
					.style("fill-opacity", function (d) {
							   return z(d.z);
						   })
					.style("fill", function (d) {
								if (nodes[d.x].group == nodes[d.y].group)
									return c[nodes[d.x].group];
								else
									return '#000'
						   })
					.on("mouseover", mouseover)
					.on("mouseout", mouseout);
		}

		function mouseover(p) {
			d3.selectAll(".row text").classed("active", function (d, i) {
				return i == p.y;
			});
			d3.selectAll(".column text").classed("active", function (d, i) {
				return i == p.x;
			});
			var nx = nodes[p.x];
			var ny = nodes[p.y];
			var pct_x = (100*p.z / nx.count).toFixed(2);
			var title = "Percent of " + nx.monkey + ": " + pct_x;
			d3.select(this).attr("title", title);

		}

		function mouseout() {
			d3.selectAll("text").classed("active", false);
		}

		d3.select("#order").on("change", function () {
			clearTimeout(timeout);
			order(this.value);
		});

		function order(value) {
			x.domain(orders[value]);

			var t = svg.transition().duration(2500);

			t.selectAll(".row")
					.delay(function (d, i) {
							   return x(i) * 4;
						   })
					.attr("transform", function (d, i) {
							  return "translate(0," + x(i) + ")";
						  })
					.selectAll(".cell")
					.delay(function (d) {
							   return x(d.x) * 4;
						   })
					.attr("x", function (d) {
							  return x(d.x);
						  });

			t.selectAll(".column")
					.delay(function (d, i) {
							   return x(i) * 4;
						   })
					.attr("transform", function (d, i) {
							  return "translate(" + x(i) + ")rotate(-90)";
						  });
		}

		var timeout = setTimeout(function () {
			order("group");
			d3.select("#order").property("selectedIndex", 2).node().focus();
		}, 5000);
	});

}


// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
function draw_stackplots(cohort_pk, matrix, name_color) {
// Be sure to include {% block extra_js %}<script src="/static/js/d3.v3.min.js" charset="utf-8"></script>{% endblock %}
// ::: http://bl.ocks.org/mbostock/4060954

var n = 20, // number of layers
    m = 200, // number of samples per layer
    stack = d3.layout.stack().offset("wiggle"),
    layers0 = stack(d3.range(n).map(function() { return bumpLayer(m); })),
    layers1 = stack(d3.range(n).map(function() { return bumpLayer(m); }));

var width = 960,
    height = 500;

var x = d3.scale.linear()
    .domain([0, m - 1])
    .range([0, width]);

var y = d3.scale.linear()
    .domain([0, d3.max(layers0.concat(layers1), function(layer) { return d3.max(layer, function(d) { return d.y0 + d.y; }); })])
    .range([height, 0]);

var color = d3.scale.linear()
    .range(["#aad", "#556"]);

var area = d3.svg.area()
    .x(function(d) { return x(d.x); })
    .y0(function(d) { return y(d.y0); })
    .y1(function(d) { return y(d.y0 + d.y); });

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

svg.selectAll("path")
    .data(layers0)
  .enter().append("path")
    .attr("d", area)
    .style("fill", function() { return color(Math.random()); });

function transition() {
  d3.selectAll("path")
      .data(function() {
        var d = layers1;
        layers1 = layers0;
        return layers0 = d;
      })
    .transition()
      .duration(2500)
      .attr("d", area);
}

// Inspired by Lee Byron's test data generator.
function bumpLayer(n) {

  function bump(a) {
    var x = 1 / (.1 + Math.random()),
        y = 2 * Math.random() - .5,
        z = 10 / (.1 + Math.random());
    for (var i = 0; i < n; i++) {
      var w = (i / n - y) * z;
      a[i] += x * Math.exp(-w * w);
    }
  }

  var a = [], i;
  for (i = 0; i < n; ++i) a[i] = 0;
  for (i = 0; i < 5; ++i) bump(a);
  return a.map(function(d, i) { return {x: i, y: Math.max(0, d)}; });
}
}
