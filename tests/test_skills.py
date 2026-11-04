import contextlib
import copy
from datetime import datetime,timedelta,timezone
import io
import json
import unittest
from unittest.mock import Mock,patch

from skills_content import RECIPES,code_case,make_event
from skills_publish import publish_batch,send_event


class SkillsContentTests(unittest.TestCase):
    def test_payload_limits_options_and_ids(self):
        identifiers=set()
        for index in range(5005):
            event=make_event(index)
            self.assertNotIn(event['id'],identifiers)
            identifiers.add(event['id'])
            if event['kind']=='quiz':
                self.assertLessEqual(len(event['question'].encode('utf-16-le'))//2,300)
                self.assertEqual(len(set(event['options'])),4)
                self.assertTrue(all(1<=len(value)<=100 for value in event['options']))
                self.assertLessEqual(len(event['explanation']),200)
                self.assertLessEqual(event['explanation'].count('\n'),2)
                self.assertIn(event['correct'],range(4))
            else:
                from editorial.build_pack import plain_text
                self.assertLessEqual(len(plain_text(event['caption']).encode('utf-16-le'))//2,1024)

    def test_python_answers_match_execution_across_variations(self):
        for recipe in RECIPES:
            if recipe[1]!='Python':
                continue
            for a in (7,10,31,100):
                with self.subTest(recipe=recipe[0],a=a):
                    code,expected,_=code_case(recipe[0],a)
                    stream=io.StringIO()
                    with contextlib.redirect_stdout(stream):
                        exec(code,{})
                    self.assertEqual(stream.getvalue().strip(),expected)

    def test_module_varies_formats_and_keeps_correct_rule(self):
        for recipe_index,recipe in enumerate(RECIPES):
            start=5+recipe_index*5
            events=[make_event(start+i) for i in range(5)]
            self.assertEqual([e['kind'] for e in events],['photo','quiz','photo','quiz','photo'])
            rule=events[3]
            self.assertEqual(rule['options'][rule['correct']],recipe[5])
            _,answer,_=code_case(recipe[0],7)
            quiz=events[1]
            self.assertEqual(quiz['options'][quiz['correct']],answer.replace('\n',' / '))


class SkillsDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,4,17,20,tzinfo=timezone.utc)
        self.state={'next_index':5,'last_sent_at':(self.now-timedelta(minutes=11)).isoformat(),'pending':None,'batch':None}

    def test_ten_minute_windows_and_batch_size(self):
        send=Mock(return_value={'message_id':100})
        publish_batch(self.state,self.now,send,Mock(),pause=lambda _:None)
        publish_batch(self.state,self.now+timedelta(minutes=5),send,Mock(),pause=lambda _:None)
        self.assertEqual(send.call_count,5)
        publish_batch(self.state,self.now+timedelta(minutes=10),send,Mock(),pause=lambda _:None)
        self.assertEqual(send.call_count,10)
        self.assertEqual(self.state['next_index'],15)

    def test_unknown_delivery_does_not_duplicate(self):
        send=Mock(side_effect=[{'message_id':100},TimeoutError()])
        with self.assertRaises(TimeoutError):
            publish_batch(self.state,self.now,send,Mock(),pause=lambda _:None)
        self.assertEqual(self.state['next_index'],6)
        retry=Mock()
        with self.assertRaises(RuntimeError):
            publish_batch(self.state,self.now+timedelta(minutes=10),retry,Mock(),pause=lambda _:None)
        retry.assert_not_called()

    def test_failed_reservation_prevents_send(self):
        send=Mock()
        with self.assertRaises(RuntimeError):
            publish_batch(self.state,self.now,send,Mock(side_effect=RuntimeError('push failed')),pause=lambda _:None)
        send.assert_not_called()

    def test_quiz_payload_uses_correct_option_and_picture(self):
        event=make_event(6)
        with patch('skills_publish.api',return_value={'message_id':100,'poll':{'type':'quiz'}}) as api:
            result=send_event('test-token',-100,event)
        args=api.call_args
        self.assertEqual(args.args[:2],('test-token','sendPoll'))
        self.assertEqual(args.kwargs['correct_option_ids'],[event['correct']])
        self.assertEqual(args.kwargs['options'][event['correct']]['text'],event['options'][event['correct']])
        self.assertEqual(args.kwargs['media']['type'],'photo')
        self.assertEqual(result['message_id'],100)
