"use strict";

const { MissingRequestStartError } = require("./errors");

class RequestCalculator {
  /**
   * @param {object} env Rack-style env or a Node request (`headers`, optional `requestBodyWait`)
   * @param {{ readDev?: () => boolean, random?: () => number }} [options]
   */
  constructor(env, options = {}) {
    this.env = env || {};
    this.readDev = options.readDev || (() => process.env.DYNOSCALE_DEV === "true");
    this.random = options.random || Math.random;
  }

  requestQueueTime(timeNow = new Date()) {
    const now = toDate(timeNow);
    let requestStart;
    if (this.readDev()) {
      // DYNOSCALE_DEV stands in for the Heroku router header. The delay is
      // 0..100 seconds, matching `(rand * 100).ceil` in the Ruby agent.
      const secondsAgo = Math.ceil(this.random() * 100);
      requestStart = String(now.getTime() - secondsAgo * 1000);
    } else {
      requestStart = readRequestStart(this.env);
    }

    if (requestStart == null) throw new MissingRequestStartError();

    const match = String(requestStart).match(/[0-9]+/);
    if (!match) throw new MissingRequestStartError();

    // Heroku sends epoch milliseconds. Integer division matches Ruby's
    // `to_i / 1000`, so the web metric is whole seconds.
    const startAt = integerDivide(Number(match[0]), 1000);
    const elapsed = now.getTime() / 1000 - startAt;
    return integerDivide(elapsed, 1) + toInt(readBodyWait(this.env));
  }
}

function readRequestStart(env) {
  if (env["HTTP_X_REQUEST_START"] != null && env["HTTP_X_REQUEST_START"] !== "") {
    return first(env["HTTP_X_REQUEST_START"]);
  }
  return readHeader(env.headers || env, "x-request-start");
}

function readBodyWait(env) {
  if (env["puma.request_body_wait"] != null && env["puma.request_body_wait"] !== "") {
    return env["puma.request_body_wait"];
  }
  if (env.requestBodyWait != null && env.requestBodyWait !== "") return env.requestBodyWait;
  return 0;
}

function readHeader(headers, name) {
  if (!headers || typeof headers !== "object") return undefined;
  if (typeof headers.get === "function") {
    const fromGet = headers.get(name);
    if (fromGet != null && fromGet !== "") return first(fromGet);
  }
  const target = name.toLowerCase();
  for (const [key, value] of Object.entries(headers)) {
    if (key.toLowerCase() === target && value != null && value !== "") return first(value);
  }
  return undefined;
}

function first(value) {
  return Array.isArray(value) ? value[0] : value;
}

function toDate(value) {
  if (value instanceof Date) return value;
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Date(value < 1e12 ? value * 1000 : value);
  }
  throw new TypeError("Expected a Date or unix timestamp");
}

// Ruby integer division truncates toward zero.
function integerDivide(value, divisor) {
  const quotient = value / divisor;
  return quotient < 0 ? Math.ceil(quotient) : Math.floor(quotient);
}

function toInt(value) {
  if (value == null || value === false || value === "") return 0;
  if (value === true) return 1;
  const parsed = typeof value === "number" ? value : Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed)) return 0;
  return parsed < 0 ? Math.ceil(parsed) : Math.floor(parsed);
}

module.exports = { RequestCalculator, integerDivide, toInt };
