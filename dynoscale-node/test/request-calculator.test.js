"use strict";

const { describe, it, beforeEach, afterEach } = require("node:test");
const assert = require("node:assert/strict");
const { RequestCalculator } = require("../src/request-calculator");
const { MissingRequestStartError } = require("../src/errors");

const NOW = new Date("2021-11-11T10:51:00-05:00");

describe("RequestCalculator#requestQueueTime", () => {
  let previousDev;

  beforeEach(() => {
    previousDev = process.env.DYNOSCALE_DEV;
    process.env.DYNOSCALE_DEV = "false";
  });

  afterEach(() => {
    restore("DYNOSCALE_DEV", previousDev);
  });

  it("raises when X-Request-Start is missing", () => {
    const calculator = new RequestCalculator({ HTTP_X_REQUEST_START: null });
    assert.throws(() => calculator.requestQueueTime(NOW), MissingRequestStartError);
  });

  it("converts a millisecond timestamp into whole seconds of queue time", () => {
    const requestStart = `${Math.floor(NOW.getTime() / 1000) * 1000 - 1}`;
    const calculator = new RequestCalculator({ HTTP_X_REQUEST_START: requestStart });
    assert.equal(calculator.requestQueueTime(NOW), 1);
  });

  it("accepts the t= prefix used by Heroku and nginx", () => {
    const requestStart = `t=${Math.floor(NOW.getTime() / 1000) * 1000 - 1}`;
    const calculator = new RequestCalculator({ HTTP_X_REQUEST_START: requestStart });
    assert.equal(calculator.requestQueueTime(NOW), 1);
  });

  it("reads the Node header name", () => {
    const requestStart = `t=${Math.floor(NOW.getTime() / 1000) * 1000 - 1}`;
    const calculator = new RequestCalculator({ headers: { "x-request-start": requestStart } });
    assert.equal(calculator.requestQueueTime(NOW), 1);
  });

  it("adds puma request body wait, matching the Ruby agent", () => {
    const requestStart = `${Math.floor(NOW.getTime() / 1000) * 1000 - 1}`;
    const calculator = new RequestCalculator({
      HTTP_X_REQUEST_START: requestStart,
      "puma.request_body_wait": 1,
    });
    assert.equal(calculator.requestQueueTime(NOW), 2);
  });

  it("adds requestBodyWait from a Node request", () => {
    const requestStart = `${Math.floor(NOW.getTime() / 1000) * 1000 - 1}`;
    const calculator = new RequestCalculator({
      headers: { "x-request-start": requestStart },
      requestBodyWait: 1,
    });
    assert.equal(calculator.requestQueueTime(NOW), 2);
  });

  it("simulates up to 100 seconds of queue time in dev mode", () => {
    const calculator = new RequestCalculator(
      {},
      { readDev: () => true, random: () => 0.5 }
    );
    assert.equal(calculator.requestQueueTime(NOW), 50);
  });
});

function restore(name, value) {
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
}
