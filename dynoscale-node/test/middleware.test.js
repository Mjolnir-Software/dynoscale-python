"use strict";

const { describe, it, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const { createMiddleware } = require("../src/middleware");
const { Recorder } = require("../src/recorder");
const { Reporter } = require("../src/reporter");
const { RequestCalculator } = require("../src/request-calculator");
const { ApiWrapper } = require("../src/api-wrapper");
const { Bullmq } = require("../src/workers/bullmq");

const ENV_KEYS = ["SKIP_DYNOSCALE_AGENT", "DYNOSCALE_DEV", "DYNOSCALE_URL", "DYNO", "HEROKU_APP_NAME"];

describe("middleware", () => {
  let previous;

  beforeEach(async () => {
    previous = {};
    for (const key of ENV_KEYS) {
      previous[key] = process.env[key];
      delete process.env[key];
    }
    Recorder.reset();
    await Reporter.reset();
  });

  afterEach(async () => {
    for (const key of ENV_KEYS) {
      if (previous[key] === undefined) delete process.env[key];
      else process.env[key] = previous[key];
    }
    await Reporter.reset();
    Recorder.reset();
  });

  it("calls next without recording when SKIP_DYNOSCALE_AGENT is set", async () => {
    process.env.SKIP_DYNOSCALE_AGENT = "true";
    const seen = watch();
    assert.deepEqual(await invoke(seen.middleware), [200, "OK"]);
    assert.equal(seen.recorded, 0);
    assert.equal(seen.started, 0);
  });

  it("calls next and warns when DYNOSCALE_URL is missing", async () => {
    process.env.DYNO = "web.1";
    const lines = [];
    const original = console.log;
    console.log = (line) => lines.push(String(line));
    try {
      const seen = watch();
      assert.deepEqual(await invoke(seen.middleware), [200, "OK"]);
      assert.equal(seen.recorded, 0);
      assert.match(lines.join("\n"), /Missing DYNOSCALE_URL/);
    } finally {
      console.log = original;
    }
  });

  it("does nothing on a dyno other than *.1", async () => {
    process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
    process.env.DYNO = "web.2";
    const seen = watch();
    assert.deepEqual(await invoke(seen.middleware), [200, "OK"]);
    assert.equal(seen.recorded, 0);
    assert.equal(seen.started, 0);
  });

  it("does nothing when DYNO is unset outside dev mode", async () => {
    process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
    const seen = watch();
    assert.deepEqual(await invoke(seen.middleware), [200, "OK"]);
    assert.equal(seen.recorded, 0);
  });

  it("records and starts the reporter on the first dyno", async () => {
    process.env.DYNO = "web.1";
    await assertActive({ dyno: "web.1" });
  });

  it("records and starts the reporter when DYNOSCALE_DEV is true", async () => {
    process.env.DYNOSCALE_DEV = "true";
    await assertActive({ dyno: "dev.1" });
  });

  it("does not start another reporter when one is already running", async () => {
    process.env.DYNO = "web.1";
    process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
    let started = 0;
    const middleware = createMiddleware({
      record: async () => [],
      reporterRunning: () => true,
      startReporter: () => {
        started += 1;
      },
    });
    await invoke(middleware);
    assert.equal(started, 0);
  });

  it("does not record from a cluster worker other than 1", async () => {
    process.env.DYNO = "web.1";
    process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
    let recorded = 0;
    const middleware = createMiddleware({
      isReportingProcess: () => false,
      record: async () => {
        recorded += 1;
      },
    });
    await invoke(middleware);
    assert.equal(recorded, 0);
  });

  it("still calls next when the request has no X-Request-Start", async () => {
    process.env.DYNO = "web.1";
    process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
    const middleware = createMiddleware({
      startReporter: () => {
        throw new Error("reporter should not start");
      },
    });
    assert.deepEqual(await invoke(middleware, {}), [200, "OK"]);
  });
});

async function assertActive({ dyno }) {
  process.env.DYNOSCALE_URL = "https://dynoscale.example/api";
  process.env.HEROKU_APP_NAME = "example-app";
  let recordedWith;
  let startedWith;
  const middleware = createMiddleware({
    record: async (calculator, workers) => {
      recordedWith = { calculator, workers };
      return [];
    },
    reporterRunning: () => false,
    startReporter: (api) => {
      startedWith = api;
    },
  });
  assert.deepEqual(
    await invoke(middleware, { "x-request-start": `t=${Date.now()}` }),
    [200, "OK"]
  );
  assert.ok(recordedWith.calculator instanceof RequestCalculator);
  assert.ok(recordedWith.workers.includes(Bullmq));
  assert.ok(startedWith instanceof ApiWrapper);
  assert.equal(startedWith.dyno, dyno);
  assert.equal(startedWith.url, "https://dynoscale.example/api");
  assert.equal(startedWith.appName, "example-app");
}

function watch() {
  const seen = { recorded: 0, started: 0 };
  seen.middleware = createMiddleware({
    record: async () => {
      seen.recorded += 1;
      return [];
    },
    reporterRunning: () => false,
    startReporter: () => {
      seen.started += 1;
    },
  });
  return seen;
}

async function invoke(middleware, headers = { "x-request-start": `t=${Date.now()}` }) {
  let status;
  let body;
  const req = { headers };
  const res = {
    writeHead(code) {
      status = code;
    },
    end(payload) {
      body = payload;
    },
  };
  await middleware(req, res, () => {
    res.writeHead(200);
    res.end("OK");
  });
  return [status, body];
}
