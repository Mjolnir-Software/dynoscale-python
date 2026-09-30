"use strict";

const { Bullmq } = require("./bullmq");

function defaultWorkers() {
  return [Bullmq];
}

module.exports = { defaultWorkers, Bullmq };
