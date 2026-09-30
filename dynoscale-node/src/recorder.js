"use strict";

const logger = require("./logger");
const { Report } = require("./report");

// A report becomes eligible this many seconds after the first sample in it.
const REPORT_RECORDING_FREQ = 5;

class Recorder {
  static reset() {
    this.currentReport = null;
    this.reportsByTimestamp = new Map();
  }

  static get reports() {
    if (!this.reportsByTimestamp) this.reset();
    return Array.from(this.reportsByTimestamp.values());
  }

  static async record(requestCalculator, workers, currentTime = new Date()) {
    if (!this.reportsByTimestamp) this.reset();
    const now = currentTime instanceof Date ? currentTime : new Date(currentTime);
    const queueTime = requestCalculator.requestQueueTime(now);

    if (!this.currentReport) {
      this.currentReport = new Report(new Date(now.getTime() + REPORT_RECORDING_FREQ * 1000));
    }

    // Ruby treats 0 as false, so a zero-second queue time is not stored.
    // Negative queue times are stored.
    if (queueTime) {
      this.currentReport.addMeasurement(now, queueTime, "web", null);
      logger.debug(`Web measurement ${unix(now)}, ${queueTime} recorded in report.`);
    }

    for (const worker of workers || []) {
      try {
        if (!worker.enabled()) continue;
        const latencies = await worker.queueLatencies();
        for (const entry of latencies || []) {
          const [queue, latency] = entry;
          this.currentReport.addMeasurement(now, latency, `${worker.name}:${queue}`, null);
          logger.debug(
            `${worker.name} worker measurement ${unix(now)}, ${latency} recorded in report.`
          );
        }
      } catch (error) {
        logger.warn(`Could not read ${worker.name || "worker"} queue latency: ${error.message}`);
      }
    }

    this.reportsByTimestamp.set(this.currentReport.publishTimestamp.getTime(), this.currentReport);
    return this.reports;
  }

  static removePublishedReports(reports) {
    if (!this.reportsByTimestamp) this.reset();
    for (const report of reports || []) {
      const key = report.publishTimestamp.getTime();
      if (this.currentReport && this.currentReport.publishTimestamp.getTime() === key) {
        this.currentReport = null;
      }
      this.reportsByTimestamp.delete(key);
    }
  }
}

function unix(date) {
  return Math.floor(date.getTime() / 1000);
}

Recorder.reset();

module.exports = { Recorder, REPORT_RECORDING_FREQ };
