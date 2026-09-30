"use strict";

const logger = require("./logger");
const { MissingRequestStartError } = require("./errors");
const { RequestCalculator } = require("./request-calculator");
const { Recorder } = require("./recorder");
const { Reporter } = require("./reporter");
const { ApiWrapper } = require("./api-wrapper");
const { defaultWorkers, Bullmq } = require("./workers");

function createMiddleware(options = {}) {
  if (options.bullmq) Bullmq.configure(options.bullmq);

  return async function dynoscaleMiddleware(req, res, next) {
    try {
      await observe(req, options);
    } catch (error) {
      if (error instanceof MissingRequestStartError) {
        logger.debug(error.message);
      } else {
        logger.error(error && error.message ? error.message : String(error));
      }
    }
    if (typeof next === "function") next();
  };
}

async function observe(req, options) {
  const env = options.env || process.env;
  if (env.SKIP_DYNOSCALE_AGENT !== undefined) return;

  const isDev = env.DYNOSCALE_DEV === "true";
  const dyno = isDev ? "dev.1" : env.DYNO;

  if (!env.DYNOSCALE_URL) {
    console.log("Missing DYNOSCALE_URL environment variable");
    return;
  }

  const isFirstDyno = typeof env.DYNO === "string" && env.DYNO.split(".").pop() === "1";
  if (!(isDev || isFirstDyno)) return;

  const isReportingProcess = options.isReportingProcess || defaultIsReportingProcess;
  if (!isReportingProcess()) return;

  const workers = options.workers || defaultWorkers;
  const calculator = new RequestCalculator(req, {
    readDev: () => (options.env || process.env).DYNOSCALE_DEV === "true",
  });
  const record = options.record || ((calc, list) => Recorder.record(calc, list));
  await record(calculator, workers());

  const running = options.reporterRunning || (() => Reporter.running);
  if (running()) return;

  const start = options.startReporter || ((api) => Reporter.start(Recorder, api, options));
  const api = new ApiWrapper(dyno, env.DYNOSCALE_URL, env.HEROKU_APP_NAME, options.request);
  start(api);
}

function defaultIsReportingProcess() {
  const cluster = require("cluster");
  if (cluster.isWorker) return Boolean(cluster.worker && cluster.worker.id === 1);
  return true;
}

function stop() {
  Reporter.stop();
  return Bullmq.close();
}

module.exports = { createMiddleware, stop, defaultIsReportingProcess };
