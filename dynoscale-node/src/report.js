"use strict";

const { Measurement } = require("./measurement");

// Seconds. Reports older than this are expired. The Ruby agent names this
// constant in a comment as minutes, but the value and the specs treat it as
// seconds (5 * 60).
const REPORT_TTL = 5 * 60;

class Report {
  constructor(publishTimestamp) {
    this.measurements = [];
    this.publishTimestamp = toDate(publishTimestamp);
  }

  addMeasurement(currentTime, metric, source, metadata) {
    const time = toDate(currentTime);
    this.measurements.push(
      new Measurement(unixSeconds(time), metric, source, metadata)
    );
  }

  addMeasurements(measurements) {
    this.measurements.unshift(...measurements);
  }

  readyToPublish(currentTime = new Date()) {
    return this.measurements.length > 0 && this.publishTimestamp < toDate(currentTime);
  }

  expired(currentTime = new Date()) {
    const cutoff = new Date(toDate(currentTime).getTime() - REPORT_TTL * 1000);
    return this.publishTimestamp < cutoff;
  }

  toCsv() {
    return this.measurements.reduce((text, measurement) => {
      const metadata = measurement.metadata == null ? "" : measurement.metadata;
      return `${text}${measurement.timestamp},${measurement.metric},${measurement.source},${metadata}\n`;
    }, "");
  }
}

function toDate(value) {
  if (value instanceof Date) return value;
  if (typeof value === "number" && Number.isFinite(value)) {
    // Unix seconds are ~1e9; millisecond timestamps are ~1e12.
    return new Date(value < 1e12 ? value * 1000 : value);
  }
  throw new TypeError("Expected a Date or unix timestamp");
}

function unixSeconds(date) {
  return Math.floor(toDate(date).getTime() / 1000);
}

module.exports = { Report, REPORT_TTL, toDate, unixSeconds };
