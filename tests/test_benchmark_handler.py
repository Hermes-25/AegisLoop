from __future__ import annotations

from api.benchmark import handler


def test_benchmark_head_reports_ready_without_writing_a_body() -> None:
    endpoint = object.__new__(handler)
    statuses: list[int] = []
    headers: dict[str, str] = {}
    ended: list[bool] = []

    endpoint.send_response = statuses.append
    endpoint.send_header = headers.__setitem__
    endpoint.end_headers = lambda: ended.append(True)
    endpoint.wfile = None

    endpoint.do_HEAD()

    assert statuses == [200]
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert int(headers["Content-Length"]) > 0
    assert ended == [True]
