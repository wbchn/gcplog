"""

"""
import datetime
import logging
import os
import time
from typing import Any

import fluent.asyncsender
import fluent.event
import google.cloud.logging
from google.cloud.logging import _helpers
from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging.handlers.transports.background_thread import _Worker


def json_enqueue(self, record: logging.LogRecord, message, resource=None, labels=None, trace=None, span_id=None):
    entry = {
        "info": {"python_logger": record.name, **record.args},
        "severity": _helpers._normalize_severity(record.levelno),
        "resource": resource,
        "labels": labels,
        "trace": trace,
        "span_id": span_id,
        "timestamp": datetime.datetime.utcfromtimestamp(record.created),
    }
    self._queue.put_nowait(entry)


_Worker.enqueue = json_enqueue


class MixedLogging(object):
    _client: google.cloud.logging.Client
    _logger: logging.Logger
    _sender: fluent.asyncsender.FluentSender

    def __init__(
            self, module: str, stage: str,
            fluent_host: str = 'localhost',
            fluent_port: int = 24224,
            **kw):
        """
        """

        logger_name = f'{module}_{stage}'

        self._client = google.cloud.logging.Client(**kw)
        handler = CloudLoggingHandler(self._client, name=logger_name)
        self._logger = logging.getLogger(logger_name)
        self._logger.handlers = [handler]  # replace existing handlers
        self._logger.setLevel(logging.INFO)

        self._sender = fluent.asyncsender.FluentSender(
            f'persist.{logger_name}',
            host=fluent_host,
            port=fluent_port,
            timeout=3,
        )

    def _format(self, msg: Any) -> dict:
        if isinstance(msg, str):
            msg = {"message": msg}
        return msg

    def close(self):
        self._sender.close()

    def debug(self, msg: Any, **kw):
        """Write debug log to Cloud Logging."""
        return self._logger.debug(None, self._format(msg), **kw)

    def info(self, msg: Any, **kw):
        """Write info log to Cloud Logging."""
        return self._logger.info(None, self._format(msg), **kw)

    def warning(self, msg: Any, **kw):
        """Write warning log to Cloud Logging."""
        return self._logger.warning(None, self._format(msg), **kw)

    def error(self, msg: Any, **kw):
        """Write error log to Cloud Logging."""
        return self._logger.error(None, self._format(msg), **kw)

    def metric(self, tag: str, msg: dict, **kw) -> None:
        """Send metrics data to ElasticSearch"""
        payload = {
            "tag": tag,
            "@timestamp": int(time.time()),
        }
        payload.update(msg)
        return self._logger.info(None, self._format(msg), **kw)

    def persist(self, tag: str, msg: dict) -> None:
        """Save log to GCS."""
        # TODO: add insert id
        payload = {
            "tag": tag,
            "time": int(time.time()),
        }
        payload.update(msg)
        self._sender.emit(tag, payload)
