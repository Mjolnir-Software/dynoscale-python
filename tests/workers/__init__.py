import time


def rq_mock_job():
    time.sleep(0.1)
    return "rq_mock_job result"


def rq_mock_job_2():
    time.sleep(0.2)
    return "rq_mock_job_2 result"
