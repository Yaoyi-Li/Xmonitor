"use strict";


var site = {};

site.index = function (req, res) {
	var settings = global.settings.app;
	var locals = {
		metrics: mtStats.metrics,
		appSettings: JSON.stringify({ url: settings.url + "/api",
			interval: mtStats.interval,
			retry: settings.retryInterval,
			graphRanges: settings.graphRanges,
			graphRange: settings.graphRanges[0]
		})
	};

	res.render("index", { locals: locals, settings: settings });
};

module.exports = site;