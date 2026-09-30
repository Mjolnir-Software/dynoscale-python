# Dynoscale Node

Scaling agent for Node.js apps on Heroku. It reports request queue time, and optionally BullMQ queue latency, to the [Dynoscale](https://dynoscale.net) add-on.

Queue time is how long a request waits before your app starts handling it. Dynoscale scales from that signal, so a slow handler does not by itself add dynos. This package follows the same reporting protocol as [`dynoscale_ruby`](https://github.com/Mjolnir-Software/dynoscale_ruby).

Web and worker dynos have to run on Standard or Performance dynos for autoscaling to take effect.

## Getting started

1. Add the Dynoscale add-on: `heroku addons:create dscale`
2. Install the agent: `npm install dynoscale-node`
3. Mount the middleware first, before your routes.
4. Deploy.

`DYNOSCALE_URL` is set by the add-on. The agent only reports from the dyno whose name ends in `.1` (normally `web.1`).

```js
const express = require("express");
const dynoscale = require("dynoscale-node");

const app = express();
app.use(dynoscale());

app.get("/", (req, res) => {
  res.send("Hello from Express, scaled by Dynoscale!");
});

app.listen(process.env.PORT || 3000);
```

The middleware is a `(req, res, next)` function, so the same call works on Connect. With the `node:http` module, pass the request through `dynoscale()` and call your handler from `next`. See `examples/http/server.js`.

```js
const http = require("node:http");
const dynoscale = require("dynoscale-node");
const middleware = dynoscale();

http.createServer((req, res) => {
  middleware(req, res, () => {
    res.end("Hello from Node, scaled by Dynoscale!\n");
  });
}).listen(process.env.PORT || 3000);
```

Confirm the install on Heroku:

```bash
heroku run node -e "console.log(require('dynoscale-node').VERSION)"
```

## What gets sent

On each request to the `*.1` dyno the agent samples:

- **Web queue time**, in whole seconds, from the Heroku `X-Request-Start` header (`t=<epoch milliseconds>` or a bare millisecond timestamp).
- **BullMQ queue latency**, in milliseconds, for each configured queue. The source is `bullmq:<queue>`. This is read from Redis in the web process, the same way the Ruby agent reads Sidekiq and Resque.

Samples collect into one in-memory report. Five seconds after the first sample, a background loop POSTs the report as CSV to `DYNOSCALE_URL`:

```text
timestamp,metric,source,metadata
```

`timestamp` is Unix seconds. After a successful publish the agent waits 30 seconds, or whatever `config.publish_frequency` the response contains. A failed publish is retried after 15 seconds. Published fields are the dyno name (`X_DYNO`), the app name (`X_APP_NAME`, from `HEROKU_APP_NAME`), and `User-Agent: dynoscale-node;<version>`.

A missing `X-Request-Start` skips that sample. The request still reaches your app.

## BullMQ

Install BullMQ in the app (`npm install bullmq`). The adapter turns on when it can load `bullmq` and finds a Redis URL.

Name the queues in either place:

```bash
heroku config:set DYNOSCALE_BULLMQ_QUEUES=mail,pdf
```

```js
app.use(dynoscale({
  bullmq: {
    queues: ["mail", "pdf"],
    connection: process.env.REDIS_URL,
  },
}));
```

With no names configured, the agent scans Redis for BullMQ `meta` keys using the first Redis URL it finds (`REDIS_URL`, `REDIS_TLS_URL`, and the Redis Cloud, Redis To Go, OpenRedis, and RedisGreen URL variables). `DYNOSCALE_REDIS_URL` overrides that search. Set `bullmq.prefix` when the queues do not use the default `bull` prefix.

Latency is the age of the oldest waiting job. Delayed jobs are not part of that wait list.

## Environment

| Variable | Effect |
| --- | --- |
| `DYNOSCALE_URL` | Required. Publish target, set by the add-on. |
| `DYNO` | Heroku dyno name. Reporting runs only when it ends in `.1`. |
| `HEROKU_APP_NAME` | Sent as `X_APP_NAME`. Enable Heroku's `runtime-dyno-metadata` lab to set it. |
| `SKIP_DYNOSCALE_AGENT` | Any value, including an empty one, turns the agent off. Use this on review, staging, and development apps. |
| `DYNOSCALE_DEV` | Set to `true` to report even without `DYNO`. Queue time is simulated as 0–100 seconds, and publishes are not delayed. |
| `DYNOSCALE_BULLMQ_QUEUES` | Comma-separated BullMQ queue names. |
| `DYNOSCALE_REDIS_URL` | Redis URL for BullMQ, when it should not come from the provider URL. |

In a Node cluster (`node:cluster`, throng, and similar), only worker id `1` reports. A process that is not a cluster worker always reports. Pass `isReportingProcess` to replace that rule.

## Shutdown

`dynoscale.stop()` ends the publish loop and closes BullMQ clients. The loop's timer does not keep the process alive on its own; your HTTP server does.

## Development

```bash
npm test
```

Requires Node.js 18 or newer.
