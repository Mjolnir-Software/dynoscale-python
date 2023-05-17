# Changelog of `dynoscale` for Python

### 1.2.2 [TBD]
 - updated test/dev dependencies
 - adding support for TLS redis urls with self-signed certificates

### 1.2.1 [2023-03-01]
 - Fix: Limit resource consumption while reporting on extreme numbers of pending tasks.

### 1.2.0 [2023-01-08]
 - dropping support for Python 3.7, 3.8, 3.9
 - adding support for Gunicorn with Uvicorn workers, use dynoscale.uvicorn.DynoscaleUnicornWorker

### 1.1.3 [2023-01-13]

- Added support for ASGI through DynoscaleAsgiApp class
- Added options to control DS repository storage location with environment variables

### 1.1.2 [2022-05-27]

- Added logging to DynoscaleRQLogger

### 1.1.1 [2022-05-12]

- fixed issue when using GUNICORN hook (Incorrect key name in headers)

### 1.1.0 [2022-03-25]

- Support for [RQ](https://python-rq.org)

### 1.0.0 [2022-02-27]

First public release