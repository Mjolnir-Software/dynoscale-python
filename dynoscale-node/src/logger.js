"use strict";

function debugEnabled() {
  const flag = process.env.DYNOSCALE_DEV;
  return flag !== undefined && flag !== "";
}

function write(level, message) {
  const text = `dynoscale: ${message}`;
  if (level === "debug") {
    if (debugEnabled()) console.debug(text);
    return;
  }
  if (level === "error") console.error(text);
  else console.warn(text);
}

module.exports = {
  debug: (message) => write("debug", message),
  warn: (message) => write("warn", message),
  error: (message) => write("error", message),
};
