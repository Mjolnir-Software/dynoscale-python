"use strict";

const { VERSION } = require("./version");
const { toDate, unixSeconds } = require("./report");

class ApiWrapper {
  constructor(dyno, url, appName, request = defaultRequest) {
    this.dyno = dyno;
    this.url = url;
    this.appName = appName;
    this.request = request;
  }

  async publishReports(reports, currentTime = new Date()) {
    const now = toDate(currentTime);
    const headers = {
      "Content-Type": "text/csv",
      "User-Agent": `dynoscale-node;${VERSION}`,
      X_REQUEST_START: `t=${unixSeconds(now)}`,
      X_DYNO: this.dyno == null ? "" : String(this.dyno),
      X_APP_NAME: this.appName == null ? "" : String(this.appName),
    };
    const body = (reports || []).reduce((text, report) => text + report.toCsv(), "");

    let response;
    try {
      response = await this.request(this.url, { method: "POST", headers, body });
    } catch {
      response = undefined;
    }

    const status = responseStatus(response);
    const success = typeof status === "number" && status >= 200 && status < 300;
    const config = await readConfig(response);

    return {
      success,
      publishedReports: success ? reports : [],
      config,
    };
  }
}

async function defaultRequest(url, options) {
  return fetch(url, options);
}

function responseStatus(response) {
  if (!response) return undefined;
  if (typeof response.status === "number") return response.status;
  if (response.code != null && response.code !== "") return Number(response.code);
  return undefined;
}

async function readConfig(response) {
  if (!response) return {};
  let text = "";
  try {
    if (typeof response.text === "function") text = await response.text();
    else if (typeof response.body === "string") text = response.body;
  } catch {
    return {};
  }
  try {
    const parsed = JSON.parse(text || "{}");
    return (parsed && parsed.config) || {};
  } catch {
    return {};
  }
}

module.exports = { ApiWrapper };
