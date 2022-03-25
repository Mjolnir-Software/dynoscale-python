import logging

import pytest
from rq import Queue

from dynoscale.config import get_redis_urls_from_environ
from dynoscale.utils import ensure_module
from dynoscale.workers.rq_logger import (
    get_queue_time_records,
    redis_connection,
    queue_time_records_for_connection,
    DynoscaleRqLogger,
)
from workers import rq_mock_job_2, rq_mock_job

logging.basicConfig(level=logging.DEBUG)


def test_redislite_fixture_set(redislite):
    redislite.set('test_key', 'test_value')
    assert redislite.get('test_key') == b'test_value'


def test_redislite_fixture_doesnt_persist_data_between_tests(redislite):
    assert redislite.get('test_key') is None


def test_ensure_module_returns_correct_module():
    import sys
    sys_B = ensure_module('sys')
    assert sys == sys_B


def test_ensure_module_returns_none_for_non_existing_module():
    assert ensure_module('this_module_does_not_exist') is None


def test_get_redis_url_returns_an_empty_dict_when_there_are_none_in_env():
    assert get_redis_urls_from_environ() == {}


def test_get_redis_urls_from_environ_returns_url(env_set_redis_url_localhost):
    assert get_redis_urls_from_environ() == {'REDIS_URL': 'redis://127.0.0.1:6379'}


def test_get_redis_urls_prom_environ_returns_all_urls(env_set_redis_url_all):
    assert get_redis_urls_from_environ() == {
        'OPENREDIS_URL': 'redis://127.0.0.1:6379',
        'REDISCLOUD_URL': 'redis://127.0.0.1:6379',
        'REDISGREEN_URL': 'redis://127.0.0.1:6379',
        'REDISTOGO_URL': 'redis://127.0.0.1:6379',
        'REDIS_URL': 'redis://127.0.0.1:6379',
    }


def test_get_queue_time_records_doesnt_raise_with_valid_redis_urls(env_set_redis_url_all):
    records = [record for record in get_queue_time_records()]
    assert records == []


def test_get_queue_time_records_doesnt_raise_with_no_redis_urls():
    records = [record for record in get_queue_time_records()]
    assert records == []


@pytest.mark.skip(reason="no way of currently testing this")
def test_redis_connection_logs_warning_with_invalid_url(caplog):
    with caplog.at_level("WARN"):
        caplog.clear()
        with redis_connection(None):
            pass
        assert caplog.record_tuples == [
            ('dynoscale.workers.rq_logger', 30, 'Dynoscale could not connect to redis at invalid.')
        ]


def test_redis_connection_successfully_connects(redislite, redislite_url, caplog):
    with caplog.at_level("WARNING"):
        caplog.clear()
        with redis_connection(redislite_url) as c:
            pass
        assert caplog.record_tuples == []


def test_queue_time_records_for_connection_doesnt_raise(redislite):
    queue_time_records_for_connection(redislite)


def test_get_queue_time_records(env_set_redis_url_redislite, redislite):
    from workers import rq_mock_job, rq_mock_job_2

    q1 = Queue(connection=redislite)
    q1.enqueue_call(func=rq_mock_job)
    records = [record for record in get_queue_time_records()]
    assert len(records) == 1

    q1.enqueue_call(func=rq_mock_job_2)
    records = [record for record in get_queue_time_records()]
    assert len(records) == 1  # We're only logging one job (the oldest one) per queue

    q2 = Queue("second_queue", connection=redislite)
    q2.enqueue_call(func=rq_mock_job)
    records = [record for record in get_queue_time_records()]
    assert len(records) == 2


def test_dynoscale_rq_logger_log_queue_times(repo_path, env_set_redis_url_redislite, redislite):
    q1 = Queue(connection=redislite)
    q1.enqueue_call(func=rq_mock_job)

    ds_rql = DynoscaleRqLogger(repository_path=repo_path)
    ds_rql.log_queue_times()
    records = ds_rql.repository.get_all_records()
    assert len(records) == 1
    assert records[0].source == "rq:default"

    q2 = Queue("priority", connection=redislite)
    q2.enqueue_call(func=rq_mock_job_2)
    ds_rql.log_queue_times()
    records = ds_rql.repository.get_all_records()
    # We expect to see 3 records, one from last call to log_queue_times and two more now (the original again plus the new one
    assert len(records) == 3
    # There should be two records for default queue and one for priority
    default = [r for r in records if "default" in r.source]
    priority = [r for r in records if "priority" in r.source]
    assert len(default) == 2
    assert len(priority) == 1
