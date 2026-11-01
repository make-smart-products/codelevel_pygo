import contextlib
from datetime import datetime, timedelta, timezone
import io
import unittest
from unittest.mock import Mock

from content import exercise, render
from scheduled_publish import publish


class ContentTests(unittest.TestCase):
    def test_python_answers_match_execution(self):
        for index in range(0, 320, 2):
            with self.subTest(index=index):
                item = exercise(index)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exec(item['code'], {})
                self.assertEqual(output.getvalue().strip(), item['answer'])
                self.assertLess(len(render(index).encode('utf-16-le')) // 2, 4096)

    def test_post_bodies_change(self):
        posts = [render(index) for index in range(320)]
        self.assertEqual(len(set(posts)), len(posts))


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 1, 15, tzinfo=timezone.utc)
        self.state = {'next_index': 0, 'last_sent_at': (self.now-timedelta(hours=4)).isoformat(), 'pending': None}

    def test_does_not_send_if_reservation_cannot_be_saved(self):
        send = Mock()
        with self.assertRaises(RuntimeError):
            publish(self.state, self.now, send, Mock(side_effect=RuntimeError('push failed')))
        send.assert_not_called()

    def test_unknown_delivery_stays_pending_and_is_not_retried(self):
        with self.assertRaises(TimeoutError):
            publish(self.state, self.now, Mock(side_effect=TimeoutError()), Mock())
        send = Mock()
        with self.assertRaises(RuntimeError):
            publish(self.state, self.now+timedelta(hours=4), send, Mock())
        send.assert_not_called()

    def test_success_advances_and_persists_progress(self):
        snapshots = []
        publish(self.state, self.now, Mock(return_value={'message_id': 123}), lambda state: snapshots.append(dict(state)))
        self.assertIsNotNone(snapshots[0]['pending'])
        self.assertIsNone(snapshots[1]['pending'])
        self.assertEqual(self.state['next_index'], 1)

    def test_early_run_does_not_send(self):
        send = Mock()
        self.state['last_sent_at'] = (self.now-timedelta(hours=2)).isoformat()
        publish(self.state, self.now, send, Mock())
        send.assert_not_called()

    def test_delayed_previous_run_does_not_skip_next_slot(self):
        previous = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        now = datetime(2026, 11, 1, 15, 20, tzinfo=timezone.utc)
        self.state['last_sent_at'] = previous.isoformat()
        send = Mock(return_value={'message_id': 124})
        publish(self.state, now, send, Mock())
        send.assert_called_once()
