def test_assert_asserts():
    assert True


def test_pre_request_exists():
    from dynoscale.hooks.gunicorn import pre_request
    assert pre_request


def test_pre_request_doesnt_crash():
    from dynoscale.hooks.gunicorn import pre_request
    from types import SimpleNamespace
    worker = SimpleNamespace(pid=1)
    worker.pid = 1
    req = SimpleNamespace(headers={'some': 'header'})
    pre_request(worker, req=req)
    assert pre_request
