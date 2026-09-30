"use strict";

const { describe, it, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const { Reporter } = require("../src/reporter");
const { Report } = require("../src/report");

describe("Reporter", () => {
  let previousDev;

  beforeEach(() => {
    previousDev = process.env.DYNOSCALE_DEV;
    delete process.env.DYNOSCALE_DEV;
  });

  afterEach(async () => {
    await Reporter.reset();
    restore("DYNOSCALE_DEV", previousDev);
  });

  it("publishes ready reports, drops them, and waits the configured frequency", async () => {
    const report = readyReport();
    const recorder = recorderWith(report);
    const sleeps = [];
    const api = {
      async publishReports(reports) {
        assert.deepEqual(reports, [report]);
        return { success: true, publishedReports: reports, config: { publish_frequency: 45 } };
      },
    };

    await Reporter.start(recorder, api, {
      breakAfterFirstIteration: true,
      sleep: async (seconds) => {
        sleeps.push(seconds);
      },
    });

    assert.deepEqual(recorder.reports, []);
    assert.deepEqual(sleeps, [45]);
    assert.equal(Reporter.reportPublishFreq(), 45);
  });

  it("keeps reports and uses the retry delay when publish fails", async () => {
    const report = readyReport();
    const recorder = recorderWith(report);
    const sleeps = [];
    const api = {
      async publishReports() {
        return { success: false, publishedReports: [], config: {} };
      },
    };

    await Reporter.start(recorder, api, {
      breakAfterFirstIteration: true,
      sleep: async (seconds) => {
        sleeps.push(seconds);
      },
    });

    assert.equal(recorder.reports.length, 1);
    assert.deepEqual(sleeps, [15]);
  });

  it("does not publish a report that is not ready yet", async () => {
    const report = new Report(new Date(Date.now() + 60_000));
    report.addMeasurement(new Date(), 1, "web", null);
    const recorder = recorderWith(report);
    let published = false;
    const sleeps = [];

    await Reporter.start(recorder, {
      async publishReports() {
        published = true;
        return { success: true, publishedReports: [], config: {} };
      },
    }, {
      breakAfterFirstIteration: true,
      sleep: async (seconds) => {
        sleeps.push(seconds);
      },
    });

    assert.equal(published, false);
    assert.deepEqual(sleeps, [15]);
  });

  it("uses a zero delay in dev mode", async () => {
    process.env.DYNOSCALE_DEV = "true";
    const recorder = recorderWith(readyReport());
    const sleeps = [];
    await Reporter.start(recorder, {
      async publishReports(reports) {
        return { success: true, publishedReports: reports, config: {} };
      },
    }, {
      breakAfterFirstIteration: true,
      sleep: async (seconds) => {
        sleeps.push(seconds);
      },
    });
    assert.deepEqual(sleeps, [0]);
  });

  it("stays running until an in-flight publish finishes", async () => {
    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    const recorder = recorderWith(readyReport());
    const first = Reporter.start(recorder, {
      async publishReports() {
        await gate;
        return { success: true, publishedReports: [], config: {} };
      },
    }, {
      breakAfterFirstIteration: true,
      sleep: async () => {},
    });

    Reporter.stop();
    assert.equal(Reporter.running, true);
    const second = Reporter.start(recorder, {
      async publishReports() {
        throw new Error("second loop");
      },
    });
    assert.equal(second, first);
    release();
    await first;
    assert.equal(Reporter.running, false);
  });

  it("does not start a second loop while one is running", async () => {
    let release;
    const gate = new Promise((resolve) => {
      release = resolve;
    });
    const recorder = recorderWith(readyReport());
    const first = Reporter.start(recorder, {
      async publishReports() {
        await gate;
        return { success: true, publishedReports: [], config: {} };
      },
    }, {
      breakAfterFirstIteration: true,
      sleep: async () => {},
    });
    const second = Reporter.start(recorder, {
      async publishReports() {
        throw new Error("second loop");
      },
    });
    assert.equal(second, first);
    release();
    await first;
  });
});

function readyReport() {
  const report = new Report(new Date(Date.now() - 1000));
  report.addMeasurement(new Date(), 2, "web", null);
  return report;
}

function recorderWith(report) {
  return {
    reports: [report],
    removePublishedReports() {
      this.reports = [];
    },
  };
}

function restore(name, value) {
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
}
