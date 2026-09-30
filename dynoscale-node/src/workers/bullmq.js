"use strict";

const logger = require("../logger");

const REDIS_ENV_VARS = [
  "REDIS_TLS_URL",
  "REDIS_URL",
  "REDISTOGO_TLS_URL",
  "REDISTOGO_URL",
  "OPENREDIS_TLS_URL",
  "OPENREDIS_URL",
  "REDISGREEN_TLS_URL",
  "REDISGREEN_URL",
  "REDISCLOUD_TLS_URL",
  "REDISCLOUD_URL",
];

const DISCOVERY_TTL_MS = 30_000;
const PROBE_QUEUE = "__dynoscale_discover__";

class Bullmq {
  static get name() {
    return "bullmq";
  }

  static configure(options = {}) {
    this._options = { ...this._options, ...options };
  }

  static reset() {
    this._options = {};
    this._discovered = null;
    this._queues = new Map();
  }

  static enabled() {
    if (process.env.SKIP_DYNOSCALE_AGENT !== undefined) return false;
    if (!this._canLoad()) return false;
    return Boolean(this.connectionOptions());
  }

  static async queueLatencies(now = Date.now()) {
    const names = await this.queueNames();
    const results = [];
    for (const name of names) {
      try {
        const queue = this._queueFor(name);
        results.push(await latencyForQueue(queue, name, now));
      } catch (error) {
        logger.warn(`BullMQ queue "${name}" could not be read: ${error.message}`);
      }
    }
    return results;
  }

  static async close() {
    const queues = Array.from(this._queues.values());
    this._queues.clear();
    await Promise.all(
      queues.map((queue) => (typeof queue.close === "function" ? queue.close() : undefined))
    );
  }

  static connectionOptions() {
    if (this._options.connection) return this._options.connection;
    const url = process.env.DYNOSCALE_REDIS_URL || redisUrlFromEnv();
    return url ? { url } : undefined;
  }

  static async queueNames() {
    if (Array.isArray(this._options.queues) && this._options.queues.length > 0) {
      return this._options.queues.map(String);
    }
    const fromEnv = (process.env.DYNOSCALE_BULLMQ_QUEUES || "")
      .split(",")
      .map((name) => name.trim())
      .filter(Boolean);
    if (fromEnv.length > 0) return fromEnv;
    return this._discoverNames();
  }

  static _canLoad() {
    if (this._options.createQueue) return true;
    try {
      require.resolve("bullmq");
      return true;
    } catch {
      return false;
    }
  }

  static _queueFor(name) {
    if (!this._queues.has(name)) {
      const create = this._options.createQueue || defaultCreateQueue;
      this._queues.set(
        name,
        create(name, {
          connection: this.connectionOptions(),
          prefix: this._options.prefix,
        })
      );
    }
    return this._queues.get(name);
  }

  static async _discoverNames() {
    const fresh =
      this._discovered && Date.now() - this._discovered.at < DISCOVERY_TTL_MS;
    if (fresh) return this._discovered.names;
    if (!this.connectionOptions() || !this._canLoad()) return [];

    const prefix = this._options.prefix || "bull";
    const probe = this._queueFor(PROBE_QUEUE);
    try {
      const client = await probe.client;
      const names = new Set();
      let cursor = "0";
      do {
        const [next, keys] = await client.scan(cursor, "MATCH", `${prefix}:*:meta`, "COUNT", 200);
        cursor = String(next);
        const marker = `${prefix}:`;
        for (const key of keys) {
          const text = String(key);
          if (!text.startsWith(marker) || !text.endsWith(":meta")) continue;
          const name = text.slice(marker.length, -":meta".length);
          if (name && name !== PROBE_QUEUE) names.add(name);
        }
      } while (cursor !== "0");
      this._discovered = { at: Date.now(), names: Array.from(names) };
      return this._discovered.names;
    } catch (error) {
      logger.warn(`BullMQ queue discovery failed: ${error.message}`);
      return [];
    }
  }
}

function defaultCreateQueue(name, options) {
  const { Queue } = require("bullmq");
  const queueOptions = { connection: options.connection };
  if (options.prefix) queueOptions.prefix = options.prefix;
  return new Queue(name, queueOptions);
}

async function latencyForQueue(queue, name, now) {
  // BullMQ LPUSHes new jobs and workers RPOP the tail, so the oldest waiting
  // job is the last list element. asc:true asks getJobs for that end.
  const jobs = await queue.getJobs(["waiting"], 0, 0, true);
  const job = jobs && jobs[0];
  let latency = 0;
  if (job && job.timestamp != null) {
    latency = Math.ceil(now - Number(job.timestamp));
  }
  let depth = 0;
  if (typeof queue.getJobCounts === "function") {
    const counts = await queue.getJobCounts("waiting");
    depth = counts && counts.waiting ? counts.waiting : 0;
  }
  return [name, latency, depth];
}

function redisUrlFromEnv() {
  for (const name of REDIS_ENV_VARS) {
    if (process.env[name]) return process.env[name];
  }
  return undefined;
}

Bullmq.reset();

module.exports = { Bullmq, latencyForQueue, REDIS_ENV_VARS };
