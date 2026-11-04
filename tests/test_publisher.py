import contextlib
import copy
from datetime import datetime, timedelta, timezone
import io
import unittest
from unittest.mock import Mock, patch

from content import course_posts, exercise, render
from scheduled_publish import publish, send_course_post


class ContentTests(unittest.TestCase):
    def test_python_answers_match_execution(self):
        for index in range(0, 300, 2):
            with self.subTest(index=index):
                item = exercise(index)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exec(item['code'], {})
                self.assertEqual(output.getvalue().strip(), item['answer'])
                self.assertLess(len(render(index).encode('utf-16-le')) // 2, 4096)

    def test_post_bodies_change(self):
        posts = [render(index) for index in range(300)]
        self.assertEqual(len(set(posts)), len(posts))

    def test_course_has_300_ordered_posts_and_release_at_60(self):
        posts = course_posts()
        self.assertEqual(len(posts), 300)
        self.assertEqual([p['number'] for p in posts], list(range(1,301)))
        self.assertTrue(all(p['artifact_url'] for p in posts[:60]))
        self.assertTrue(all(p['implementation_status']=='learning_exercise_to_implement' for p in posts[60:]))

    def test_intro_is_five_distinct_animations_and_keeps_post_ids(self):
        posts = course_posts()[:5]
        self.assertEqual([p['id'] for p in posts], ['cl-0001','cl-0002','cl-0003','cl-0004','cl-0005'])
        self.assertEqual(len({p['animation']['path'] for p in posts}), 5)
        self.assertTrue(all(p['content_revision']=='python-go-motion-2026-11-04' for p in posts))


class MediaTests(unittest.TestCase):
    def test_animation_uses_file_id_and_caption(self):
        post = copy.deepcopy(course_posts()[0])
        post['animation']['file_id'] = 'test-file-id'
        with patch('scheduled_publish.course_posts',return_value=[post]), patch('scheduled_publish.api') as api:
            send_course_post('test-token',-100,post['html'])
        api.assert_called_once_with('test-token','sendAnimation',chat_id=-100,animation='test-file-id',
                                    caption=post['caption_html'],parse_mode='HTML')

    def test_animation_does_not_silently_become_text(self):
        post = copy.deepcopy(course_posts()[0])
        post['animation'].pop('file_id',None)
        with patch('scheduled_publish.course_posts',return_value=[post]), patch('scheduled_publish.api') as api:
            with self.assertRaises(RuntimeError):
                send_course_post('test-token',-100,post['html'])
        api.assert_not_called()


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.pause = patch('scheduled_publish.time.sleep').start()
        self.addCleanup(patch.stopall)
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
        send = Mock(side_effect=[{'message_id': n} for n in range(123,128)])
        publish(self.state, self.now, send, lambda state: snapshots.append(copy.deepcopy(state)))
        self.assertIsNotNone(snapshots[0]['pending'])
        self.assertIsNone(snapshots[1]['pending'])
        self.assertEqual(self.state['next_index'], 5)
        self.assertEqual(send.call_count, 5)
        self.assertEqual(len(snapshots), 10)
        self.assertIsNone(self.state['batch'])
        self.assertEqual(self.state['last_message_id'], 127)
        self.assertEqual(self.pause.call_count, 4)
        self.assertEqual([s['pending']['index'] for s in snapshots[::2]], list(range(5)))
        self.assertEqual(len(set(call.args[0] for call in send.call_args_list)), 5)

    def test_early_run_does_not_send(self):
        send = Mock()
        self.state['last_sent_at'] = (self.now-timedelta(minutes=30)).isoformat()
        publish(self.state, self.now, send, Mock())
        send.assert_not_called()

    def test_delayed_previous_run_does_not_skip_next_slot(self):
        previous = datetime(2026, 11, 1, 14, 30, tzinfo=timezone.utc)
        now = datetime(2026, 11, 1, 15, 20, tzinfo=timezone.utc)
        self.state['last_sent_at'] = previous.isoformat()
        send = Mock(return_value={'message_id': 124})
        publish(self.state, now, send, Mock())
        self.assertEqual(send.call_count, 5)

    def test_old_three_hour_slot_does_not_duplicate_current_hour(self):
        self.state['last_slot'] = 166077
        self.state['last_sent_at'] = (self.now-timedelta(minutes=5)).isoformat()
        send = Mock()
        publish(self.state, self.now, send, Mock())
        send.assert_not_called()

    def test_next_hour_publishes_after_previous_success(self):
        send = Mock(return_value={'message_id': 125})
        publish(self.state, self.now, send, Mock())
        publish(self.state, self.now+timedelta(minutes=5), send, Mock())
        self.assertEqual(send.call_count, 5)
        publish(self.state, self.now+timedelta(hours=1), send, Mock())
        self.assertEqual(send.call_count, 10)

    def test_failure_in_middle_preserves_progress_and_blocks_retry(self):
        send = Mock(side_effect=[{'message_id': 123}, {'message_id': 124}, TimeoutError()])
        with self.assertRaises(TimeoutError):
            publish(self.state, self.now, send, Mock())
        self.assertEqual(self.state['next_index'], 2)
        self.assertEqual(self.state['pending']['index'], 2)
        self.assertEqual(self.state['batch']['end_index'], 5)
        retry = Mock()
        with self.assertRaises(RuntimeError):
            publish(self.state, self.now+timedelta(hours=1), retry, Mock())
        retry.assert_not_called()

    def test_confirmed_partial_batch_resumes_without_repeating_sent_posts(self):
        self.state.update(next_index=2, batch={'slot':0,'end_index':5}, last_sent_at=self.now.isoformat())
        send = Mock(return_value={'message_id': 125})
        publish(self.state, self.now, send, Mock())
        self.assertEqual(send.call_count, 3)
        self.assertEqual(send.call_args_list[0].args[0], render(2))
        self.assertEqual(self.state['next_index'], 5)
        self.assertIsNone(self.state['batch'])

    def test_final_partial_batch_stops_at_end_of_course(self):
        self.state['next_index'] = 298
        send = Mock(return_value={'message_id': 500})
        publish(self.state, self.now, send, Mock())
        self.assertEqual(send.call_count, 2)
        self.assertEqual(self.state['next_index'], 300)
        publish(self.state, self.now+timedelta(hours=1), send, Mock())
        self.assertEqual(send.call_count, 2)
