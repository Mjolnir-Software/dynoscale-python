import logging
import math
import os
import time
from dataclasses import dataclass
from os.path import exists
from typing import Optional, Union, Tuple

from dynoscale.permadict import Permadict

DEFAULT_DYNOSCALE_REPOSITORY_FILENAME: str = 'dynoscale_repo.sqlite3'


@dataclass
class Record:
    timestamp: int
    metric: int
    source: str
    metadata: str


@dataclass
class RecordIn(Record):
    pass


@dataclass
class RecordOut(RecordIn):
    row_id: int


# noinspection SqlNoDataSourceInspection
# noinspection SqlResolve
class DynoscaleRepository(Permadict):
    """Storage for logs regarding the lifecycle of requests"""

    def __init__(self, path: Optional[Union[str, bytes, os.PathLike]] = None, **kwargs):
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{DynoscaleRepository.__name__}")
        self.logger.debug("__init__")
        db_filename = path if path else os.path.join(os.getcwd(), DEFAULT_DYNOSCALE_REPOSITORY_FILENAME)
        self.db_existed = exists(db_filename)
        super().__init__(db_filename)
        self._create_log_table()
        self.logger.info(f"Dynoscale {'opened' if self.db_existed else 'created'} repository {self.filename}.")

    def _create_log_table(self):
        self.logger.debug("_create_log_table")
        with self.cursor() as cur:
            cur.execute(
                'CREATE TABLE IF NOT EXISTS logs(timestamp INTEGER, metric INTEGER, source STRING, metadata STRING)'
            )

    def add_record(self, record: Record):
        self.logger.debug(f"add_record ({record.timestamp},{record.metric},{record.source},{record.metadata})")
        with self.cursor() as cur:
            cur.execute(
                'INSERT INTO logs (timestamp, metric, source, metadata) VALUES (?,?,?,?)',
                (record.timestamp, record.metric, record.source, record.metadata)
            )

    def get_all_records(self) -> Tuple[RecordOut]:
        self.logger.debug("get_all_records")
        with self.cursor() as cur:
            cur.execute("SELECT rowid, timestamp, metric, source, metadata FROM logs ORDER BY timestamp")
            rows = cur.fetchall()
            return tuple(RecordOut(row_id=r[0], timestamp=r[1], metric=r[2], source=r[3], metadata=r[4]) for r in rows)

    def delete_records(self, records: Tuple[RecordOut]):
        if not (records and isinstance(records, Tuple) and isinstance(records[0], RecordOut)):
            self.logger.debug(f"delete_records - Attempting to delete non-iterable: {records}")
            return
        self.logger.debug(f"delete_records - Deleting {len(records)} records.")
        row_id_tuples = [(r.row_id,) for r in records if hasattr(r, 'row_id')]
        with self.cursor() as cur:
            try:
                cur.executemany('DELETE FROM logs WHERE rowid = (?)', row_id_tuples)
            except Exception as e:
                self.logger.warning(f"DynoscaleRepository ran into an issue while deleting records {e}")
        self.__vacuum()

    def delete_records_before(self, t: float):
        self.logger.debug(f"delete_records_before {t}")
        with self.cursor() as cur:
            cur.execute('DELETE FROM logs WHERE timestamp < (?)', (math.ceil(t),))
        self.__vacuum()

    def delete_records_older_than(self, seconds: float):
        self.logger.debug(f"delete_records_older_than {seconds} seconds")
        self.delete_records_before(time.time() - seconds)

    def __vacuum(self):
        self.logger.debug("__vacuum")
        with self.cursor() as cur:
            cur.execute('VACUUM')
