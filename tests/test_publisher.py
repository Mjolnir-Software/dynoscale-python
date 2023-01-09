import asyncio
import logging
import threading
import time

import pytest
import requests
import responses

from dynoscale.repository import Record
from dynoscale.utils import epoch_s

logging.basicConfig(level=logging.DEBUG)


# ========================= TESTS =============================

@responses.activate
def test_responses_https(mock_url):
    responses.add(responses.GET, mock_url, json={'error': 'not found'}, status=404)
    resp = requests.get(mock_url)
    assert resp.json() == {"error": "not found"}
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == mock_url
    assert responses.calls[0].response.text == '{"error": "not found"}'


@responses.activate
def test_responses_from_another_thread(mock_url):
    responses.add(responses.GET, mock_url, status=200)

    def call():
        requests.get(mock_url)

    t = threading.Thread(target=call())
    t.start()
    t.join()
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == mock_url
    assert responses.calls[0].response.status_code == 200


def test_caplog(caplog):
    with caplog.at_level(logging.INFO):
        logging.getLogger().info("simple %s", "caplog")
    assert caplog.record_tuples == [("root", logging.INFO, "simple caplog")]


def test_publisher_exists():
    from dynoscale.publisher import DynoscalePublisher
    assert DynoscalePublisher


def test_publisher_initializes(env_valid):
    from dynoscale.publisher import DynoscalePublisher
    assert DynoscalePublisher()


def test_publisher_init_values(ds_agent, ds_publisher):
    from dynoscale.publisher import DEFAULT_PUBLISH_FREQUENCY
    ds_agent.log_queue_time(1, 1)
    assert ds_publisher.last_publish_attempt == 0
    assert ds_publisher.publish_frequency == DEFAULT_PUBLISH_FREQUENCY


def test_publisher_tick_does_nothing_without_logs(ds_agent, ds_publisher):
    from dynoscale.publisher import DEFAULT_PUBLISH_FREQUENCY
    ds_agent.log_queue_time(1, 1)
    assert not ds_publisher.last_publish_success
    assert ds_publisher.publish_frequency == DEFAULT_PUBLISH_FREQUENCY
    assert not ds_publisher.last_publish_success
    ds_publisher.tick()
    assert not ds_publisher.last_publish_success


def test_publisher_does_not_publish_with_just_old_data(ds_publisher, mocked_responses):
    from dynoscale.publisher import DEFAULT_PUBLISH_FREQUENCY
    ds_publisher.repository.add_record(Record(123456789, 0, 'web', ''))
    ds_publisher.publish_frequency = 0
    ds_publisher.tick()

    assert ds_publisher.publish_frequency == DEFAULT_PUBLISH_FREQUENCY
    assert not ds_publisher.last_publish_success
    assert len(mocked_responses.calls) == 0


def test_publisher_does_not_publish_if_config_invalid_missing_dyno(env_invalid_missing_dyno, mocked_responses):
    from dynoscale.publisher import DynoscalePublisher

    publisher = DynoscalePublisher()
    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert not publisher.last_publish_attempt


def test_publisher_does_not_publish_if_config_invalid_missing_url(env_invalid_missing_url, mocked_responses):
    from dynoscale.publisher import DynoscalePublisher

    publisher = DynoscalePublisher()
    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert not publisher.last_publish_attempt


def test_publisher_can_handle_non_ok_response(env_valid, mocked_responses):
    from dynoscale.publisher import DynoscalePublisher
    publisher = DynoscalePublisher()
    mocked_responses.add(responses.POST, publisher.config.url, status=500, json={})

    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert not publisher.last_publish_success


def test_publisher_publishes_after_first_response(env_valid, mocked_responses):
    from dynoscale.publisher import DynoscalePublisher
    publisher = DynoscalePublisher()
    mocked_responses.add(responses.POST, publisher.config.url, status=200)

    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert publisher.last_publish_attempt
    assert publisher.last_publish_success


def test_publisher_publishes_data_with_forced_publish_frequency(ds_publisher, mocked_api_200_no_config):
    ds_publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    ds_publisher.publish_frequency = 0
    ds_publisher.tick()
    assert ds_publisher.last_publish_attempt


def test_publisher_request_payload_format(ds_publisher, mocked_api_200_no_config):
    timestamp = epoch_s()
    ds_publisher.publish_frequency = 0
    ds_publisher.repository.add_record(Record(timestamp, 0, 'web', ''))
    ds_publisher.tick()
    assert ds_publisher.last_publish_attempt
    assert mocked_api_200_no_config.calls[0].request.body.decode() == f'{timestamp},0,web,\r\n'


def test_publisher_updates_publish_frequency(ds_publisher, mocked_api_200_with_publish_frequency_30):
    timestamp = epoch_s()
    ds_publisher.publish_frequency = 0
    ds_publisher.repository.add_record(Record(timestamp, 0, 'web', ''))
    ds_publisher.tick()
    assert ds_publisher.publish_frequency == 30
    assert ds_publisher.last_publish_attempt


def test_publisher_publishes_what_logger_logs(
        env_valid,
        ds_repository,
        ds_publisher,
        mocked_api_200_no_config
):
    ds_repository.add_record(Record(epoch_s(), 0, 'web', ''))
    ds_publisher.publish_frequency = 0
    ds_publisher.tick()
    assert ds_publisher.last_publish_attempt


def test_publisher_doesnt_publish_old_logs(
        env_valid,
        ds_repository,
        ds_publisher
):
    from dynoscale.publisher import MAX_RECORD_AGE
    ds_repository.add_record(Record(epoch_s() - MAX_RECORD_AGE, 0, 'web', ''))
    ds_publisher.publish_frequency = 0
    ds_publisher.tick()
    assert not ds_publisher.last_publish_success
    assert not ds_repository.get_all_records()


def test_publisher_doesnt_crash_when_prepublish_hook_raises_exception(
        env_valid,
        ds_repository,
        ds_publisher,
        mocked_responses,
        caplog
):
    ds_publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    ds_publisher.publish_frequency = 0

    def do_raise():
        raise AttributeError("ERROR")

    ds_publisher.pre_publish_hook = do_raise

    mocked_responses.add(responses.POST, ds_publisher.config.url, status=200, json={})

    with caplog.at_level("WARNING"):
        caplog.clear()
        ds_publisher.tick()
        assert ds_publisher.last_publish_attempt
        assert caplog.record_tuples == [
            ('dynoscale.publisher', 40, 'DynoscalePublisher encountered error while executing pre_publish_hook: ERROR')
        ]


@pytest.mark.asyncio
@responses.activate
async def test_async():
    sleep_time = 0.1
    before = time.time()
    await asyncio.sleep(sleep_time)
    after = time.time()
    assert before < after
    assert before + sleep_time < after
