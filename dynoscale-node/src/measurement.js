"use strict";

class Measurement {
  constructor(timestamp, metric, source, metadata) {
    this.timestamp = timestamp;
    this.metric = metric;
    this.source = source;
    this.metadata = metadata == null ? "" : metadata;
  }
}

module.exports = { Measurement };
