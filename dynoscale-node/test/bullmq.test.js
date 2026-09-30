"use strict";

const { describe, it, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const { Bullmq, latencyForQueue } = require("../src/workers/bullmq");

describe("BullMQ adapter", () => {
  let previous;

  beforeEach(() => {
    previous = {
      SKIP_DYNOSCALE_AGENT: process.env.SKIP_DYNOSCALE_AGENT,
      REDIS_URL: process.env.REDIS_URL,
      DYNOSCALE_BULLMQ_QUEUES: process.env.DYNOSCALE_BULLMQ_QUEUES,
    };
    delete process.env.SKIP_DYNOSCALE_AGENT;
    delete process.env.REDIS_URL;
    delete process.env.DYNOSCALE_BULLMQ_QUEUES;
    Bullmq.reset();
  });

  afterEach(async () => {
    await Bullmq.close();
    Bullmq.reset();
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  });

  it("is disabled when bullmq is not installed and no test queue factory is set", () => {
    process.env.REDIS_URL = "redis://127.0.0.1:6379";
    let resolved = true;
    try {
      require.resolve("bullmq");
      resolved = true;
    } catch {
      resolved = false;
    }
    assert.equal(Bullmq.enabled(), resolved);
  });

  it("is disabled when SKIP_DYNOSCALE_AGENT is set", () => {
    process.env.SKIP_DYNOSCALE_AGENT = "1";
    Bullmq.configure({
      connection: { url: "redis://127.0.0.1:6379" },
      createQueue: () => ({}),
    });
    assert.equal(Bullmq.enabled(), false);
  });

  it("is disabled without a redis connection", () => {
    Bullmq.configure({ queues: ["mail"], createQueue: () => ({}) });
    assert.equal(Bullmq.enabled(), false);
  });

  it("reports the oldest waiting job age in milliseconds", async () => {
    const now = 5_000;
    const queue = {
      async getJobs(types, start, end, asc) {
        assert.deepEqual(types, ["waiting"]);
        assert.equal(start, 0);
        assert.equal(end, 0);
        assert.equal(asc, true);
        return [{ timestamp: 1_200 }];
      },
      async getJobCounts() {
        return { waiting: 3 };
      },
    };
    assert.deepEqual(await latencyForQueue(queue, "mail", now), ["mail", 3800, 3]);
  });

  it("reports zero latency when the queue is empty", async () => {
    const queue = {
      async getJobs() {
        return [];
      },
      async getJobCounts() {
        return { waiting: 0 };
      },
    };
    assert.deepEqual(await latencyForQueue(queue, "mail", 1000), ["mail", 0, 0]);
  });

  it("samples each configured queue", async () => {
    process.env.DYNOSCALE_BULLMQ_QUEUES = "mail,pdf";
    Bullmq.configure({
      connection: { url: "redis://127.0.0.1:6379" },
      createQueue(name) {
        return {
          async getJobs() {
            return [{ timestamp: name === "mail" ? 1000 : 1500 }];
          },
          async getJobCounts() {
            return { waiting: 1 };
          },
          async close() {},
        };
      },
    });
    const rows = await Bullmq.queueLatencies(5000);
    assert.deepEqual(rows, [
      ["mail", 4000, 1],
      ["pdf", 3500, 1],
    ]);
  });
});
