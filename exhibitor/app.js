"use strict";

const config = require("konphyg")(__dirname + "/config/");
const express = require("express");

global.appPath = __dirname;
global.settings = { app: config("server-setting.json") };

var routes = {};
routes.site = require("./routes/site");

var app = module.exports = express.createServer();

app.get("/api/:range?", mtStats);
app.get("/", routes.site.index);

app.listen(settings.app.localPort);
console.log("We're up on port %d in %s mode.", app.address().port, app.settings.env);