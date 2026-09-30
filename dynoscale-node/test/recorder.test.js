"use strict";

const { describe, it, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const { Recorder } = require("../src/recorder");
const { Report } = require("../src/report");

describe("Recorder", () => {
  beforeEach(() => {
    Recorder.reset();
  });

  it("creates one report for the first sample", async () => {
    const reports = await Recorder.record(calculator(1), []);
    assert.equal(reports.length, 1);
    assert.ok(reports[0] instanceof Report);
  });

  it("appends later samples to the same report", async () => {
    await Recorder.record(calculator(1), []);
    const reports = await Recorder.record(calculator(1), []);
    assert.equal(reports.length, 1);
    assert.equal(reports[0].measurements.length, 2);
  });

  it("stores the web queue time", async () => {
    const reports = await Recorder.record(calculator(4), []);
    assert.equal(reports[0].measurements[0].metric, 4);
    assert.equal(reports[0].measurements[0].source, "web");
    assert.equal(reports[0].measurements[0].metadata, "");
  });

  it("skips a zero web queue time and still samples workers", async () => {
    const worker = {
      name: "bullmq",
      enabled: () => true,
      queueLatencies: async () => [["mail", 25, 2]],
    };
    const reports = await Recorder.record(calculator(0), [worker]);
    assert.equal(reports[0].measurements.length, 1);
    assert.equal(reports[0].measurements[0].source, "bullmq:mail");
    assert.equal(reports[0].measurements[0].metric, 25);
  });

  it("ignores a disabled worker and a worker that throws", async () => {
    const workers = [
      { name: "off", enabled: () => false, queueLatencies: async () => [["a", 1, 0]] },
      {
        name: "broken",
        enabled: () => true,
        queueLatencies: async () => {
          throw new Error("redis down");
        },
      },
    ];
    const reports = await Recorder.record(calculator(3), workers);
    assert.deepEqual(
      reports[0].measurements.map((measurement) => measurement.source),
      ["web"]
    );
  });

  it("returns the stored reports", async () => {
    await Recorder.record(calculator(1), []);
    assert.equal(Recorder.reports.length, 1);
    assert.ok(Recorder.reports[0] instanceof Report);
  });

  it("deletes a report whose publish timestamp matches", async () => {
    await Recorder.record(calculator(1), []);
    Recorder.removePublishedReports(Recorder.reports);
    assert.deepEqual(Recorder.reports, []);
  });

  it("keeps a report whose publish timestamp does not match", async () => {
    await Recorder.record(calculator(1), []);
    Recorder.removePublishedReports([{ publishTimestamp: new Date(1) }]);
    assert.equal(Recorder.reports.length, 1);
  });
});

function calculator(queueTime) {
  return { requestQueueTime: () => queueTime };
}
