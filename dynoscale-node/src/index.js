"use strict";

const { VERSION } = require("./version");
const { createMiddleware, stop } = require("./middleware");

function dynoscale(options) {
  return createMiddleware(options);
}

module.exports = dynoscale;
module.exports.dynoscale = dynoscale;
module.exports.VERSION = VERSION;
module.exports.stop = stop;
