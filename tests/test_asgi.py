import logging
from pprint import pprint

import pytest
from asgiref.typing import (
    Scope,
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGI3Application,
    ASGIReceiveEvent,
    HTTPRequestEvent,
)
from starlette.responses import Response

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def asgi_app():
    from starlette.applications import Starlette
    from starlette.routing import Route

    async def home(_):
        return Response("Hello from Starlette, scaled by Dynoscale!", media_type='text/plain')

    yield Starlette(debug=True, routes=[Route('/', endpoint=home, methods=['GET'])])


@pytest.fixture
def _asgi_app() -> ASGI3Application:
    async def asgi(scope, receive, send):
        print("\nScope:")
        pprint(scope)
        print("\nReceive:")
        pprint(receive)

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, world!"})

    return asgi


@pytest.fixture
def asgi_receive_callable() -> ASGIReceiveCallable:
    async def callable() -> HTTPRequestEvent:
        return HTTPRequestEvent()

    return callable


@pytest.fixture
def asgi_send_callable() -> ASGISendCallable:
    async def callable(ASGISendEvent) -> None:
        pprint("SEND SEND SEND")

    return callable


@pytest.fixture
def asgi_scope_http() -> Scope:
    return {
        'type': "http",
        'headers': {
            "HTTP_X_REQUEST_START": "1234123434"
        }
    }


@pytest.fixture
def asgi_scope_websocket() -> Scope:
    return {
        'type': "websocket",
        'headers': {
            "HTTP_X_REQUEST_START": "1111111111"
        }
    }


@pytest.fixture
def asgi_scope_lifespan() -> Scope:
    return {
        'type': "lifespan",
    }


def test_dynoscale_asgi_app_init_doesnt_crash_with_valid_settings(env_valid, asgi_app):
    from dynoscale.asgi import DynoscaleAsgiApp
    DynoscaleAsgiApp(asgi_app)


def test_dynoscale_asgi_app_init_doesnt_crash_with_invalid_settings(env_invalid_missing_dyno, asgi_app):
    from dynoscale.asgi import DynoscaleAsgiApp
    DynoscaleAsgiApp(asgi_app)


def test_dynoscale_asgi_app_call_doesnt_crash_with_valid_settings(
        env_valid,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)


def test_dynoscale_asgi_app_call_doesnt_crash_with_invalid_settings(
        env_invalid_missing_dyno,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)


def test_dynoscale_asgi_app_call_doesnt_crash_ever(
        env_invalid_missing_dyno,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    ds_app.config = None
    ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)


def test_dynoscale_asgi_app_log_queue_time_doesnt_crash_with_valid_settings(
        env_invalid_missing_dyno,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)
    ds_app.log_queue_time(asgi_scope_http['headers'])


def test_dynoscale_asgi_app_log_queue_time_doesnt_crash_with_invalid_settings(
        env_valid,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable,
        caplog
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)
    with caplog.at_level('INFO'):
        caplog.clear()
        ds_app.log_queue_time({})
        assert caplog.record_tuples
        assert len(caplog.record_tuples) == 1
        assert caplog.record_tuples == [
            ('dynoscale.asgi.DynoscaleAsgiApp', 20, 'log_queue_time - Can not calculate queue time.')]


@pytest.mark.asyncio
async def test_dynoscale_asgi_logs_queue_time(
        env_valid,
        asgi_app,
        asgi_scope_http,
        asgi_receive_callable,
        asgi_send_callable,
        caplog,
        ds_repository
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        await ds_app(asgi_scope_http, asgi_receive_callable, asgi_send_callable)
        assert caplog.record_tuples
        assert len(ds_repository.get_all_records()) == 1


@pytest.mark.asyncio
async def test_dynoscale_asgi_doesnt_log_queue_time_for_websocket_scope_type(
        env_valid,
        asgi_app,
        asgi_scope_websocket,
        asgi_receive_callable,
        asgi_send_callable,
        caplog,
        ds_repository
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        await ds_app(asgi_scope_websocket, asgi_receive_callable, asgi_send_callable)
        assert caplog.record_tuples
        pprint(caplog.record_tuples)
        assert caplog.record_tuples[0][2] == "__call__"
        assert caplog.record_tuples[1][2] == "Scope type is not `http`."
        assert ds_repository.get_all_records() == ()


@pytest.mark.asyncio
async def test_dynoscale_asgi_doesnt_attempt_to_log_queue_time_for_lifespan_scope_type(
        env_valid,
        asgi_app,
        asgi_scope_lifespan,
        asgi_receive_callable,
        asgi_send_callable,
        caplog,
        ds_repository
):
    from dynoscale.asgi import DynoscaleAsgiApp
    ds_app = DynoscaleAsgiApp(asgi_app)
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        await ds_app(asgi_scope_lifespan, asgi_receive_callable, asgi_send_callable)
        assert caplog.record_tuples
        pprint(caplog.record_tuples)
        assert caplog.record_tuples[0][2] == "__call__"
        assert caplog.record_tuples[1][2] == "Scope type is not `http`."
        assert ds_repository.get_all_records() == ()
