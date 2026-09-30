"use strict";

const logger = require("./logger");

const REPORT_PUBLISH_FREQ = 30;
const REPORT_PUBLISH_RETRY_FREQ = 15;

class Reporter {
  static start(recorder, apiWrapper, options = {}) {
    if (this.running) return this._task;
    this.running = true;
    this._stopped = false;
    this._wake = null;
    this._task = this._loop(recorder, apiWrapper, options);
    return this._task;
  }

  static get running() {
    return Boolean(this._running);
  }

  static set running(value) {
    this._running = Boolean(value);
  }

  static stop() {
    // Leave `running` set until the loop exits so a request cannot start a
    // second publisher while this one is still finishing a POST.
    this._stopped = true;
    if (this._wake) this._wake();
  }

  static async reset() {
    const task = this._task;
    this.stop();
    if (task) await task.catch(() => {});
    this.config = null;
    this._task = null;
    this._wake = null;
    this._stopped = false;
    this.running = false;
  }

  static reportPublishFreq(env = process.env) {
    if (env.DYNOSCALE_DEV === "true") return 0;
    const freq = this.config && this.config.publish_frequency;
    if (freq) {
      const parsed = Number.parseInt(freq, 10);
      return parsed || REPORT_PUBLISH_FREQ;
    }
    return REPORT_PUBLISH_FREQ;
  }

  static reportPublishRetryFreq(env = process.env) {
    return env.DYNOSCALE_DEV === "true" ? 0 : REPORT_PUBLISH_RETRY_FREQ;
  }

  static async _loop(recorder, apiWrapper, options) {
    const sleep = options.sleep || ((seconds) => this._sleep(seconds));
    try {
      do {
        if (this._stopped) break;
        const reports = recorder.reports || [];
        const ready = reports.some((report) => report.readyToPublish());
        if (ready) {
          try {
            const { success, publishedReports, config } = await apiWrapper.publishReports(reports);
            if (this._stopped) break;
            if (success) {
              recorder.removePublishedReports(publishedReports);
              this.config = config;
              logger.debug("Report publish was successful");
              await sleep(this.reportPublishFreq());
            } else {
              logger.error("Report publish failed");
              await sleep(this.reportPublishRetryFreq());
            }
          } catch (error) {
            logger.error(`Report publish failed: ${error.message}`);
            if (!this._stopped) await sleep(this.reportPublishRetryFreq());
          }
        } else if (!this._stopped) {
          await sleep(this.reportPublishRetryFreq());
        }
        if (options.breakAfterFirstIteration) break;
      } while (!this._stopped);
    } finally {
      this.running = false;
    }
  }

  static _sleep(seconds) {
    return new Promise((resolve) => {
      // A zero delay means "do not wait for the production interval".
      // Sleeping a real 0ms would busy-spin the event loop.
      const delayMs = seconds > 0 ? seconds * 1000 : 50;
      const timer = setTimeout(resolve, delayMs);
      if (typeof timer.unref === "function") timer.unref();
      this._wake = () => {
        clearTimeout(timer);
        resolve();
      };
    });
  }
}

Reporter.running = false;
Reporter.config = null;

module.exports = { Reporter, REPORT_PUBLISH_FREQ, REPORT_PUBLISH_RETRY_FREQ };
