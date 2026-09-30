"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");
const { ApiWrapper } = require("../src/api-wrapper");
const { Report } = require("../src/report");
const { VERSION } = require("../src/version");

describe("ApiWrapper#publishReports", () => {
  const reports = [sampleReport()];

  it("yields the published reports and config when the response is 2xx", async () => {
    const wrapper = new ApiWrapper("web.1", "https://dynoscale.example/api", "example-app", async () => ({
      code: 200,
      body: '{ "config": { "publish_frequency": 30 } }',
    }));
    const result = await wrapper.publishReports(reports, new Date("2021-11-11T10:51:00-05:00"));
    assert.equal(result.success, true);
    assert.equal(result.publishedReports, reports);
    assert.deepEqual(result.config, { publish_frequency: 30 });
  });

  for (const status of [504, 503, 400]) {
    it(`yields no published reports when the status is ${status}`, async () => {
      const wrapper = new ApiWrapper("web.1", "https://dynoscale.example/api", "example-app", async () => ({
        code: status,
        body: '{ "config": { "publish_frequency": 30 } }',
      }));
      const result = await wrapper.publishReports(reports);
      assert.equal(result.success, false);
      assert.deepEqual(result.publishedReports, []);
      assert.deepEqual(result.config, { publish_frequency: 30 });
    });
  }

  it("treats a network error as a failed publish", async () => {
    const wrapper = new ApiWrapper("web.1", "https://dynoscale.example/api", "example-app", async () => {
      throw new Error("socket hang up");
    });
    const result = await wrapper.publishReports(reports);
    assert.equal(result.success, false);
    assert.deepEqual(result.publishedReports, []);
    assert.deepEqual(result.config, {});
  });

  it("posts csv with the Ruby agent's header names", async () => {
    let captured;
    const server = http.createServer((req, res) => {
      const chunks = [];
      req.on("data", (chunk) => chunks.push(chunk));
      req.on("end", () => {
        captured = {
          method: req.method,
          headers: req.headers,
          body: Buffer.concat(chunks).toString("utf8"),
        };
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end('{"config":{"publish_frequency":15}}');
      });
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    try {
      const { port } = server.address();
      const now = new Date("2021-11-11T10:51:00-05:00");
      const wrapper = new ApiWrapper("web.1", `http://127.0.0.1:${port}/report`, "example-app");
      const result = await wrapper.publishReports(reports, now);
      assert.equal(result.success, true);
      assert.equal(captured.method, "POST");
      assert.equal(captured.headers["content-type"], "text/csv");
      assert.equal(captured.headers["user-agent"], `dynoscale-node;${VERSION}`);
      assert.equal(captured.headers.x_request_start, `t=${Math.floor(now.getTime() / 1000)}`);
      assert.equal(captured.headers.x_dyno, "web.1");
      assert.equal(captured.headers.x_app_name, "example-app");
      assert.equal(captured.body, reports[0].toCsv());
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  });
});

function sampleReport() {
  const report = new Report(new Date("2021-11-11T10:51:00-05:00"));
  report.addMeasurement(new Date("2021-11-11T10:50:00-05:00"), 2, "web", null);
  return report;
}
