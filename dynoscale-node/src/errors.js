"use strict";

class MissingRequestStartError extends Error {
  constructor() {
    super("Missing X-Request-Start");
    this.name = "MissingRequestStartError";
  }
}

module.exports = { MissingRequestStartError };
