document.addEventListener("DOMContentLoaded", init);
var colors = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854'];
var jobs   = ["farmer", "wood burner", "wood cutter", "miner", "blacksmith"]
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

var HEADERCOL = "#cc0";

var datas = {}; // rowname: {<row's data>}
var rows = [];

var legendselector = "#legends";
function addrow(rowname) {
	d3.select(legendselector)
	  .append("tr")
	  .attr("id", rowname+"legend")
	  .selectAll("td")
	  .data(_.union([HEADERCOL], colors))
	  .enter()
	  .append("td")
	  .text(function(d, i){if (i==0) return rowname; return "";})
	  .attr("class", function(d, i){if (i==0) return null; return names[i-1];})
	  .style("background-color", function(d){return d;});
}


function drawGraph(graphid, limits, src) {
	var graphselector = "#" + graphid;
	// add a row to the legends
	addrow(graphid);
	rows.push(graphid);
	// draw actual graph
	var svg = d3.select(graphselector);
	d3.json(src, function(e, d){
		datas[graphid] = d;
		var xscale = d3.scale.linear()
				   .domain([0, d.food.length])
				   .range([marginleft, w-marginright]);
		var yscale = d3.scale.linear()
					   .domain([0, limits.y])
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
	   	   .attr("x1", marginleft).attr("y1", -1000)
	   	   .attr("x2", marginleft).attr("y2", h-marginbot)
	   	   .attr("transform", "translate(0, 0)");
		    svg.on("mousemove", function(){
		    	moveverticalline(this, xscale);});
	})
}

function init() {
	// init table
	d3.select(legendselector)
	  .append("tr")
	  .selectAll("td")
	  .data(_.union([["type", HEADERCOL]], _.zip(names, colors)))
	  .enter()
	  .append("td")
	  .style("background-color", function(d){return d[1];})
	  .text(function(d){return d[0];});

	// might as well draw graphs here
	drawGraph("prices", {y:60}, "raw/prices.json");
	drawGraph("demand", {y:15}, "raw/buys.json");
	drawGraph("supply", {y:500}, "raw/sells.json");
	drawGraph("jobs", {y:5}, "raw/agents.json");
}

function moveverticalline(container, xscale) {
	var x = d3.mouse(container)[0]-marginleft;
	// transform to data coordinates
	datax = xscale.invert(x+marginleft);
	datax = Math.round(datax);
	// show new data
	d3.select("#roundcounter").text(datax);
	for (row_i in rows) {
		var rowname = rows[row_i];
		d3.select("#" + rowname).select(".verticalline").attr("transform", 
			"translate(" + x + ",0)"); // move line to graph pos
		var table = d3.select("#" + rowname + "legend");
		for (i in names) {
			var name = names[i];
			table.select("." + name).text(datas[rowname][name][datax].toFixed(1));
		}
	}
	
}