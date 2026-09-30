"use strict";

const http = require("node:http");
const dynoscale = require("../../src");

const middleware = dynoscale();

const server = http.createServer((req, res) => {
  middleware(req, res, () => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Hello from Node, scaled by Dynoscale!\n");
  });
});

const port = Number(process.env.PORT || 3000);
server.listen(port, () => {
  console.log(`listening on ${port}`);
});
