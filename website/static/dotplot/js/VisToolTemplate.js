var VTTGlobal = {
	inputSpec: undefined, 
	currentPage: "#first",
	inputStatus: {},
	blobs: {},
	loadedData: {},
	layout: {},
	spinnerStack: 0,
};

// System for navigation bar links
function changePage(page) {
	d3.selectAll(".page").style("display","none");
	d3.selectAll(".page_tab").classed("active", false);

	VTTGlobal.currentPage = page;
	d3.select(VTTGlobal.currentPage).style("display", "block");
	d3.select(VTTGlobal.currentPage+"_tab").classed("active", true);
}

// System for communicating messages to the user
function showMessage(message, sentiment) {
	
	if (message !== undefined) {
		var look = R.contains(sentiment, ["success","warning","danger","info"]) ? sentiment : "info";

		var alert = d3.select("#messagesContainer")
			.append("div")
				.attr("class","alert alert-" + look +" alert-dismissable")
				.attr("role","alert");
		alert.append("a")
			.attr("href","#")
			.attr("class","close")
			.attr("data-dismiss","alert")
			.attr("aria-label","close")
			.html("&times;");
		alert.append("p")
			.html(message);
	} else {
		// use empty message as a sign to clear all alerts
		d3.select("#messagesContainer").html("");
	}
}

// Spinner for showing that something is loading
function showSpinner(bool, variable, reset) {
	
	// Stack of tasks, so when multiple files are loading, we only increment and decrement
	if (reset) {
		VTTGlobal.spinnerStack = 0;
	} else {
		if (bool) {
			VTTGlobal.spinnerStack += 1;
		} else {
			VTTGlobal.spinnerStack -= 1;
		}
	}

	if (VTTGlobal.spinnerStack > 0) {
		// wait a bit before actually showing spinner
		setTimeout(function() {
			// check again in case the stack is now empty
			if (VTTGlobal.spinnerStack > 0) {
				d3.select("#spinner").style("display", "block");
			}
		}, 100);
	} else {
		d3.select("#spinner").style("display", "none");
	}

	// d3.select("#spinner").style("display", function() {
	// 	if (VTTGlobal.spinnerStack > 0) {
	// 		return "block";
	// 	} else {
	// 		return "none";
	// 	}
	// });

	

	// // Simple on/off
	// d3.select("#spinner").style("display", function() {
	// 	if (bool) {
	// 		return "block";
	// 	} else {
	// 		return "none";
	// 	}
	// });
}

function setExamples(examples) {
	var baseURL = location.protocol + '//' + location.host + location.pathname;


	d3.select("#examples").selectAll("a").data(examples).enter().append("a")
	.attr("href", function(d) {return baseURL + d.urlSuffix})
	.html(function(d) {return d.name})
	.property("title", function(d) {return d.hover});

}

// Set up a system for reading and parsing data
function readTSVorCSV(source, inputType, variable) {
	VTTGlobal.inputStatus[variable] = "in progress";
	showSpinner(true, variable);

	if (VTTGlobal.inputSpec[variable].many) {
		if (VTTGlobal.loadedData[variable] === undefined) {
			VTTGlobal.loadedData[variable] = [];
		}
	} else {
		VTTGlobal.loadedData[variable] = undefined;
	}
	
	if (inputType === "url") {
		Papa.parse(source, {
			download: true,
			header: true,
			dynamicTyping: true,
			skipEmptyLines: true,
			complete: function(parsed) {
				setInputData(parsed.data, variable);
			},
			before: function() {
				console.log("Loading file from URL");
			},
			error: function(err) {
				VTTGlobal.inputStatus[variable] = "error";
				showSpinner(false, variable);
				showMessage("Failed to load file from URL. Make sure this URL is correct and publicly accessible, and check the console for specific errors.", "danger");
			}
		});
	} else if (inputType === "File") {
		if (variable.size > 10000000) {
			showMessage("Loading large file may take a while.", "warning");
		}
		Papa.parse(source, {
			header: true,
			dynamicTyping: true,
			skipEmptyLines: true,
			complete: function(parsed) {
				if (parsed.errors.length > 0) {
					VTTGlobal.inputStatus[variable] = "error";
					showSpinner(false, variable);
					showMessage("Errors parsing " + variable + " file: " + parsed.errors.map(function(d) {return d.message}).filter(function onlyUnique(value, index, self) { return self.indexOf(value) === index}).join(". "), "danger");
				} else {
					setInputData(parsed.data, variable);
				}
			}
		});
	}
}

function saveDontRead(source, inputType, variable) {
	showSpinner(true, variable);
	VTTGlobal.inputStatus[variable] = "success";
	setInputData(source, variable);
}

function getRandomAccess(source, inputType, variable) {

	if (inputType === "url") {
		showSpinner(true, variable);

		var request = new XMLHttpRequest();

		request.open('GET', source, true);
		request.responseType = "blob";
		request.onload = function() {
			// console.log("For", variable + ": Found file of size " + Math.round(request.response.size/1024/1024*100)/100 + "MB.")
			// Convert Blob to File
			var blob = request.response;
			blob.lastModifiedDate = new Date();
			blob.name = source.split("/").reverse()[0];

			VTTGlobal.blobs[variable] = blob;

			var randomAccessFunction = function(startByte, endByte, asyncCallback) {
				var reader = new FileReader();
				reader.readAsBinaryString(VTTGlobal.blobs[variable].slice(startByte, endByte));
				reader.onload = function(event) {
					asyncCallback(event.target.result);
				}
			}
			setInputData(randomAccessFunction, variable);
		};

		request.send();

	} else if (inputType === "File") {
		VTTGlobal.blobs[variable] = source;
		showSpinner(true, variable);

		var randomAccessFunction = function(startByte, endByte, asyncCallback) {
			var reader = new FileReader();
			reader.readAsBinaryString(VTTGlobal.blobs[variable].slice(startByte, endByte));
			reader.onload = function(event) {
				asyncCallback(event.target.result);
			}
		}
		setInputData(randomAccessFunction, variable);
	}
}

function readAsString(source, inputType, variable) {
	VTTGlobal.inputStatus[variable] = "in progress";
	VTTGlobal.loadedData[variable] = undefined;
	showSpinner(true, variable);

	if (inputType === "url") {
		var request = new XMLHttpRequest();
		request.open('GET', source, true);

		request.onload = function() {
			if (request.status >= 200 && request.status < 400) {
				// Success!
				setInputData(request.responseText, variable);
			} else {
				// We reached our target server, but it returned an error
				VTTGlobal.inputStatus[variable] = "error";
				showMessage("Could not download file because the server returned an error: " + request.status, "danger");
			}
		};

		request.onerror = function() {
			// There was a connection error of some sort
			VTTGlobal.inputStatus[variable] = "error";
			showMessage("There was an error connecting to the server to download the file at " + source, "danger");
		};

		request.send();
	} else if (inputType === "File") {
		if (source.size > 10000000) {
			showMessage("Loading large file may take a while.", "warning");
		}
		var reader = new FileReader();
		reader.readAsText(source);
		reader.onload = function(event) {
			setInputData(event.target.result, variable);
		}
	}
}


// Create input fields based on the inputSpec
function setInputSpec(inputSpec) {
	// Set up the input panel to automatically create a UI for the user to load those inputs
	VTTGlobal.inputSpec = inputSpec;

	var _input_panel = new InputPanel({
		element: d3.select("#inputPanel"),
		spec: inputSpec,
	});
}

function setInputData(data, variable) {
	
	// If you need input validation to make sure the data has the right format, do it here before setting VTTGlobal.loadedData
	// You can also apply any transformations to the data before setting VTTGlobal.loadedData

	if (VTTGlobal.inputSpec[variable].many) {
		VTTGlobal.loadedData[variable].push(data);
	} else {
		VTTGlobal.loadedData[variable] = data;
	}
	
	VTTGlobal.inputStatus[variable] = "success";
	
	// You can set some rules here to launch the visualization as soon as the required inputs are available
	// If you have optional inputs, you can instead call launchVisualization() in the onclick event of a button that the user clicks when they are satisfied with all their inputs

	var allRequiredVariablesLoaded = true;
	for (var key in VTTGlobal.inputSpec) {
		if (VTTGlobal.inputSpec[key].required && VTTGlobal.loadedData[key] === undefined) {
			allRequiredVariablesLoaded = false;
		}
	}

	var inputsInProgress = false;
	if (allRequiredVariablesLoaded) {
		for (var key in VTTGlobal.inputStatus) {
			if (VTTGlobal.inputStatus[key] == "in progress") {
				inputsInProgress = true;
				console.log("Waiting on", key);
			}
		}
		if (!inputsInProgress) {
			launchVisualization();
		}
	}

	showSpinner(false, variable);
}


// Measure the width and height of the screen
var w = window,
	d = document,
	e = d.documentElement,
	g = d.getElementsByTagName('body')[0];


VTTGlobal.layout = {
	svg: {
		width: (w.innerWidth || e.clientWidth || g.clientWidth)*0.99,
		height: (w.innerHeight || e.clientHeight || g.clientHeight)*0.80
	},
	margin: {
		top: 100,
		left: 80,
		right: 20,
		bottom: 10,
	}
};

VTTGlobal.layout.inner = {
	width: VTTGlobal.layout.svg.width - VTTGlobal.layout.margin.left - VTTGlobal.layout.margin.right,
	height: VTTGlobal.layout.svg.height - VTTGlobal.layout.margin.top - VTTGlobal.layout.margin.bottom
};



function launchVisualization() {
	changePage("#main");
	d3.select("#main_tab").style("display", "block");


	main(VTTGlobal.loadedData); // inside app.js <-- fill out the main() function inside app.js to edit the visualization itself

}
