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
    logging.getLogger().info("simple %s", "caplog")
    assert caplog.record_tuples == [("root", logging.INFO, "simple caplog")]


def test_publisher_exists():
    from dynoscale.publisher import DynoscalePublisher
    assert DynoscalePublisher


def test_publisher_initializes(env_valid):
    from dynoscale.publisher import DynoscalePublisher
    assert DynoscalePublisher()


def test_publisher_init_with_path(env_valid, repo_path):
    from dynoscale.publisher import DynoscalePublisher
    publisher = DynoscalePublisher(repository_path=repo_path)
    assert publisher
    assert publisher.repository.filename == repo_path


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


def test_publisher_does_not_publish_if_config_invalid(env_invalid, repo_path, mocked_responses, mock_url):
    from dynoscale.publisher import DynoscalePublisher

    publisher = DynoscalePublisher(repository_path=repo_path, api_url=mock_url)
    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert not publisher.last_publish_attempt


def test_publisher_can_handle_non_ok_response(env_valid, repo_path, mocked_responses, mock_url):
    from dynoscale.publisher import DynoscalePublisher
    mocked_responses.add(responses.POST, mock_url, status=500, json={})

    publisher = DynoscalePublisher(repository_path=repo_path, api_url=mock_url)
    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert not publisher.last_publish_success


def test_publisher_publishes_after_first_response(env_valid, repo_path, mocked_responses, mock_url):
    from dynoscale.publisher import DynoscalePublisher
    mocked_responses.add(responses.POST, mock_url, status=200)

    publisher = DynoscalePublisher(repository_path=repo_path, api_url=mock_url)
    publisher.repository.add_record(Record(epoch_s(), 0, 'web', ''))
    publisher.tick()
    assert publisher.last_publish_attempt


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


@pytest.mark.asyncio
@responses.activate
async def test_async():
    sleep_time = 0.1
    before = time.time()
    await asyncio.sleep(sleep_time)
    after = time.time()
    assert before < after
    assert before + sleep_time < after
