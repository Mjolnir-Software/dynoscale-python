import asyncio
import logging
import time
from pprint import pprint

import pytest
import requests
import responses

logging.basicConfig(level=logging.DEBUG)


# ========================= TESTS =============================

def test_upload_payload_exits_and_logs_on_empty_payload(
        caplog,
        mock_url,
        mocked_responses
):
    from dynoscale.publisher import upload_payload
    with caplog.at_level('DEBUG'):
        upload_payload(mock_url, b"", '')
        assert caplog.record_tuples
        assert len(caplog.record_tuples) == 2
        assert caplog.record_tuples[1] == (
            "dynoscale.publisher", logging.DEBUG, "upload_payload  - empty payload, exiting")


def test_config_from_response_valid_int(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": 123}})
    assert extract_config_response(requests.post(mock_url)).publish_frequency == 123


def test_config_from_response_valid_float(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": 123.456}})
    assert extract_config_response(requests.post(mock_url))
    assert pytest.approx(extract_config_response(requests.post(mock_url)).publish_frequency) == 123.456


def test_config_from_response_valid_string_int(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": "123"}})
    assert extract_config_response(requests.post(mock_url))


def test_config_from_response_negative_string_int(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": "-123"}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_valid_string_float(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": "123.456"}})
    assert extract_config_response(requests.post(mock_url))


def test_config_from_response_invalid_negative_string_float(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": "-123.456"}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_config_true(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": True})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_config_false(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": False})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_missing_publish_frequency(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_publish_frequency_true(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": True}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_publish_frequency_false(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": False}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_publish_frequency_array(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": []}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_publish_frequency_object(mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, json={"config": {"publish_frequency": {}}})
    assert not extract_config_response(requests.post(mock_url))


def test_config_from_response_logs_error_and_returns_non_on_no_json(caplog, mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response
    mocked_responses.add(responses.POST, mock_url, status=200)
    resp = requests.post(mock_url)
    with caplog.at_level(logging.ERROR):
        config = extract_config_response(resp)
        assert not config
        first = caplog.record_tuples[0]
        pprint(caplog)
        assert first[0] == "dynoscale.publisher"
        assert first[1] == logging.ERROR
        assert "extract_config_response" in first[2]
        assert "Error parsing response as JSON" in first[2]
        caplog.clear()


def test_config_from_response_doesnt_log_error_on_empty(caplog, mock_url, mocked_responses):
    from dynoscale.publisher import extract_config_response

    mocked_responses.add(responses.POST, mock_url, status=200, json={})
    resp = requests.post(mock_url)
    with caplog.at_level(logging.ERROR):
        config = extract_config_response(resp)
        assert not config
        assert not caplog.record_tuples
        caplog.clear()


def test_dynoscale_agent_complains_about_invalid_environment(env_invalid, caplog):
    from dynoscale.agent import DynoscaleAgent
    with caplog.at_level(logging.WARNING):
        ds_agent = DynoscaleAgent()
        assert caplog.record_tuples
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples[0][1] == logging.WARNING
        assert "invalid config" in caplog.record_tuples[0][2]

    caplog.clear()
    with caplog.at_level(logging.INFO):
        ds_agent.log_queue_time(123, 123)
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples[0][1] == logging.INFO
        assert "Throwing away" in caplog.record_tuples[0][2]


@pytest.mark.asyncio
@responses.activate
async def test_async():
    sleep_time = 0.1
    before = time.time()
    await asyncio.sleep(sleep_time)
    after = time.time()
    assert before < after
    assert before + sleep_time < after
