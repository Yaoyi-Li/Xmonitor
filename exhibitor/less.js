const less = require("less");
const fs = require("fs");
const t = fs.readFileSync("./public/stylesheets/custom.less", "utf8");

less.render(t, function (e, css) {
	if (e) return console.error(e);
	fs.writeFileSync("./public/stylesheets/custom.css", css, "utf8");
	console.log("done");
});