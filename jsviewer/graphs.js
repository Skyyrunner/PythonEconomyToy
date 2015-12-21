document.addEventListener("DOMContentLoaded", init);
var colors = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854'];
var names  = ['food','fuel','wood', 'ore', 'tools'];
var colFromName = {};
for (x in names) {
	colFromName[names[x]] = colors[x];
}
var w = 700;
var h = 300;
var marginleft = 30;
var marginbot = 30;
var margintop = 30;
var marginright = 10;

function drawGraph(graphselector, tableselector, src) {
	var tableselection = d3.select(tableselector);
	var rows = tableselection
	  .selectAll("span")
	  .data(_.pairs(colFromName))
	  .enter()
	  .append("tr")
	  .attr("class", "legend")
	  .style("background-color", function(d){return d[1];});
	rows.append("td")
	    .text(function(d){return d[0];});
    rows.append("td")
    	.attr("class", function(d){return d[0];})
    	.text(" ");
	var svg = d3.select(graphselector);
	d3.json(src, function(e, d){
		var xscale = d3.scale.linear()
				   .domain([0, d.food.length])
				   .range([marginleft, w-marginright]);
		var yscale = d3.scale.linear()
					   .domain([0, 60])
					   .range([h-marginbot, margintop]);
		var xaxis  = d3.svg.axis().scale(xscale).orient("bottom");
		var yaxis  = d3.svg.axis().scale(yscale).orient("left");
		var line = d3.svg.line()
					 .x(function(d, i){return xscale(i);})
					 .y(function(d)   {return yscale(d);});
	    var lines = svg.append("g").attr("class", "lines");
		for (key in d) {
			lines.append("path")
			   .datum(d[key])
			   .attr("class", "line")
			   .attr("d", line)
			   .style("stroke", colFromName[key]);
		}
		svg.append("g").attr("class", "x axis").call(xaxis)
	       .attr("transform", "translate(0, " + (h-marginbot) + ")");
	    svg.append("g").attr("class", "y axis").call(yaxis)
	       .attr("transform", "translate(" + marginleft + ",0)");
	   	svg.append("line").attr("class", "verticalline")
	   	   .attr("x1", marginleft).attr("y1", margintop)
	   	   .attr("x2", marginleft).attr("y2", h-marginbot)
	   	   .attr("transform", "translate(0, 0)");
		    svg.on("mousemove", function(){
		    	moveverticalline(this, tableselection, xscale, d);});
	})
}

function init() {
	// might as well draw graphs here
	drawGraph("#prices", "#pricelegends", "raw/prices.json");
}

function moveverticalline(container, table, xscale, data) {
	var x = d3.mouse(container)[0]-marginleft;
	// transform to data coordinates
	datax = xscale.invert(x+marginleft);
	datax = Math.round(datax);
	d3.select(container).select(".verticalline").attr("transform", 
		"translate(" + x + ",0)"); // move line to graph pos
	// also show new data
	for (i in names) {
		var name = names[i];
		table.select("." + name).text(data[name][datax].toFixed(1));
	}
}