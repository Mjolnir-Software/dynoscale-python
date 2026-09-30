"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { Measurement } = require("../src/measurement");
const { Report, REPORT_TTL } = require("../src/report");

const PUBLISH_AT = new Date("2021-11-11T10:51:00-05:00");
const MEASURED_AT = new Date("2021-11-11T10:50:00-05:00");

describe("Report", () => {
  it("adds a measurement", () => {
    const report = new Report(PUBLISH_AT);
    report.addMeasurement(MEASURED_AT, 1, "", "");
    assert.equal(report.measurements.length, 1);
    assert.equal(report.measurements[0].metric, 1);
    assert.equal(report.measurements[0].timestamp, Math.floor(MEASURED_AT.getTime() / 1000));
  });

  it("prepends measurements", () => {
    const report = new Report(PUBLISH_AT);
    report.addMeasurement(MEASURED_AT, 1, "web", "");
    const extra = new Measurement(1, 2, "web", "");
    report.addMeasurements([extra]);
    assert.equal(report.measurements[0], extra);
    assert.equal(report.measurements.length, 2);
  });

  it("is ready once the publish time has passed and a measurement exists", () => {
    const report = new Report(PUBLISH_AT);
    report.addMeasurements([new Measurement(1, 1, "web", "")]);
    assert.equal(report.readyToPublish(new Date("2021-11-11T10:55:00-05:00")), true);
    assert.equal(report.readyToPublish(new Date("2021-11-11T10:50:00-05:00")), false);
  });

  it("is not ready without measurements", () => {
    const report = new Report(new Date("2021-11-11T10:50:00-05:00"));
    assert.equal(report.readyToPublish(new Date("2021-11-11T10:55:00-05:00")), false);
  });

  it("expires REPORT_TTL seconds after the publish time", () => {
    const current = new Date("2021-11-11T10:55:00-05:00");
    const expired = new Report(new Date(current.getTime() - (REPORT_TTL + 1) * 1000));
    const fresh = new Report(new Date(current.getTime() - (REPORT_TTL - 1) * 1000));
    assert.equal(expired.expired(current), true);
    assert.equal(fresh.expired(current), false);
  });

  it("serializes measurements as csv", () => {
    const report = new Report(PUBLISH_AT);
    const measurement = new Measurement(Math.floor(MEASURED_AT.getTime() / 1000), 1, "web", "");
    report.addMeasurements([measurement]);
    assert.equal(
      report.toCsv(),
      `${measurement.timestamp},${measurement.metric},${measurement.source},${measurement.metadata}\n`
    );
  });
});
