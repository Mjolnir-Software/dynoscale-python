import csv
import logging
import os
import time
from dataclasses import dataclass
from io import StringIO
from json import JSONDecodeError
from typing import Optional, Union, Iterable, Callable

import requests
from requests import Session, PreparedRequest, Response, Request

from dynoscale import __version__
from dynoscale.config import Config
from dynoscale.repository import DynoscaleRepository, RecordOut

MAX_RECORD_AGE = 300.0  # Records older than this will be discarded before each upload
DEFAULT_PUBLISH_FREQUENCY = 30.0  # Minimum time between publishing records
KEY_LAST_PUBLISH_ATTEMPT = 'publish_last_attempt'
KEY_LAST_PUBLISH_SUCCESS = 'publish_last_success'
KEY_PUBLISH_FREQUENCY = 'publish_frequency'

logger = logging.getLogger(__name__)


@dataclass
class ConfigResponse:
    publish_frequency: float


def csv_from_records(records: Iterable[RecordOut]) -> bytes:
    """Generates a csv formatted string from Records"""
    buffer = StringIO()
    csv_writer = csv.writer(buffer)
    csv_writer.writerows([(r.timestamp, r.metric, r.source, r.metadata) for r in records])
    return buffer.getvalue().encode()


def dump_prepared_request(req: PreparedRequest, file=None):
    logger.debug("dump_prepared_request")
    print(
        '{}\r\n{}\r\n\r\n{}'.format(
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body.decode(),
        ),
        file=file
    )


def extract_config_response(response: Response) -> Optional[ConfigResponse]:
    logger.debug("extract_config_response")
    try:
        pf = response.json().get('config', {}).get("publish_frequency")
        return ConfigResponse(publish_frequency=float(pf)) \
            if pf and not isinstance(pf, bool) and float(pf) >= 0 \
            else None
    except JSONDecodeError as e:
        logger.error(f"extract_config_response - Error parsing response as JSON {e} : {response.text}")
    except AttributeError as e:
        logger.error(f"extract_config_response - Attribute error {e} : {response.text}")


def upload_payload(url: str, payload: bytes, dyno: str, session: Optional[Session] = None) -> Optional[Response]:
    response = None
    try:
        logger.debug("upload_payload")
        session = session if session else requests.Session()
        if not payload:
            logger.debug("upload_payload  - empty payload, exiting")
            return
        headers = {
            'Content-Type': 'text/csv',
            'User-Agent': f"dynoscale-python;{__version__}",
            'HTTP_X_DYNO': dyno
        }
        method = 'POST'
        prepared: PreparedRequest = session.prepare_request(
            Request(method=method, url=url, headers=headers, data=payload)
        )

        if logger.isEnabledFor(level=logging.DEBUG):
            dump_prepared_request(prepared)

        response = session.send(prepared)
        req_size = len(prepared.headers) + len(prepared.body)
        if response.ok:
            logger.info(f"Dynoscale successfully uploaded {req_size}bytes with status code {response.status_code}.")
        else:
            logger.warning(f"Dynoscale received status code {response.status_code} after uploading {req_size} bytes.")
    except Exception as e:
        logger.error(f"Dynoscale failed to upload data with and exception: {e}")
    finally:
        return response


class DynoscalePublisher:

    @property
    def last_publish_attempt(self) -> float:
        return self.repository.get(KEY_LAST_PUBLISH_ATTEMPT, 0)  # 0 here means never even though it really is 1970

    @last_publish_attempt.setter
    def last_publish_attempt(self, t: Optional[float]):
        self.repository[KEY_LAST_PUBLISH_ATTEMPT] = t

    @property
    def last_publish_success(self) -> Optional[float]:
        return self.repository.get(KEY_LAST_PUBLISH_SUCCESS, None)

    @last_publish_success.setter
    def last_publish_success(self, t: float):
        self.repository[KEY_LAST_PUBLISH_SUCCESS] = t

    @property
    def publish_frequency(self) -> float:
        freq = self.repository.get('publish_frequency')
        if not freq:
            freq = DEFAULT_PUBLISH_FREQUENCY
            self.publish_frequency = DEFAULT_PUBLISH_FREQUENCY
        return freq

    @publish_frequency.setter
    def publish_frequency(self, seconds: float):
        self.repository[KEY_PUBLISH_FREQUENCY] = seconds

    def __init__(self, repository_path: Optional[Union[str, bytes, os.PathLike]] = None):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscalePublisher.__name__}")
        self.config: Config = Config()
        self.repository: DynoscaleRepository = DynoscaleRepository(repository_path)
        self.session: Session = Session()
        self.pre_publish_hook: Optional[Callable] = None

    def tick(self):
        # check if we should publish at all
        if self.should_publish():
            # if we have a valid pre_publish_hook call it safely
            if callable(self.pre_publish_hook):
                try:
                    self.pre_publish_hook()
                except Exception as e:
                    logger.error(f"DynoscalePublisher encountered error while executing pre_publish_hook: {e}")
            # and attempt to publish
            self.publish()

    def should_publish(self) -> bool:
        return self.last_publish_attempt + self.publish_frequency < time.time()

    def publish(self):
        # First prune the log of old records
        self.repository.delete_records_older_than(MAX_RECORD_AGE)
        # then check if the config is even valid and return if it isn't
        if self.config.is_not_valid:
            self.logger.warning("Can not publish with invalid config.")
            return
        # if config is valid, store the time we grabbed records from db
        start_time = time.time()
        # if it is valid, store the time of the last attempt publish, which is now
        self.last_publish_attempt = start_time
        records = self.repository.get_all_records()
        # if there are no records to be published exit
        if not records:
            self.logger.info("There is nothing to publish to Dynoscale.")
            return
        # otherwise, upload the records and
        self.logger.info(f"Will publish {len(records)} records to Dynoscale.")
        response = upload_payload(self.config.url, csv_from_records(records), self.config.dyno, self.session)
        # if the upload failed, exit
        if not (isinstance(response, Response) and response.ok):
            self.logger.warning("Error publishing to Dynoscale.")
            return
        self.logger.debug("publish - response ok")
        # since it was successful store the start_time
        self.last_publish_success = start_time
        # and delete all successfully uploaded logs
        self.repository.delete_records(records)
        # and attempt to grab config from the response
        config_response = extract_config_response(response)
        # if we received config response, and it has a new publish_frequency store it
        if config_response:
            self.logger.debug(f"publish - received config response: {config_response}")
            if config_response.publish_frequency != self.publish_frequency:
                self.publish_frequency = config_response.publish_frequency
                self.logger.info(
                    f"Dynoscale updated publish frequency, next publish in {config_response.publish_frequency}s.")
