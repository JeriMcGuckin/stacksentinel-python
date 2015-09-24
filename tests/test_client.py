"""
Tests for Stack Sentinel client.
"""
import json
from StackSentinel import StackSentinelMiddleware, StackSentinelClient, StackSentinelError

import unittest
import sys

class TestStackSentinel(unittest.TestCase):
    def setUp(self):
        pass

    def test_serialize_object(self):
        class RegularClass(object):
            pass

        class ObjectThatCantBeRepr(object):
            def __repr__(self):
                raise RuntimeError

        x = RegularClass()
        y = StackSentinelClient._serialize_object(x)
        if not (y.startswith('<') and 'RegularClass' in y):
            self.fail('Unexpected result from _serialize_object: %r' % y)

        x = ObjectThatCantBeRepr()
        y = StackSentinelClient._serialize_object(x)
        self.failUnlessEqual(y, '<Cannot Be Serialized>')

    def test_get_sys(self):
        client = StackSentinelClient('', '', 'unittest')
        sys_info = client._get_sys_info()
        self.failUnlessEqual(sys.path, sys_info['path'])

    def test_get_machine_info(self):
        client = StackSentinelClient('', '', 'unittest')
        machine_info = client._get_machine_info()
        self.failUnless('hostname' in machine_info)

    def test_generate_request(self):
        client = StackSentinelClient('', '', 'unittest')
        (request, payload) = client._generate_request(
            environment='unitest',
            error_message='TEST ERROR MESSAGE',
            error_type='TEST ERROR TYPE',
            return_feedback_urls=True,
            state={
                'test': range(100)
            },
            tags=['cheese'],
            traceback=[]
        )
        payload_parsed = json.loads(payload)
        self.failUnless('return_feedback_urls' in payload)

    def test_handle_exception(self):
        client = StackSentinelClient('', '', 'unittest')
        try:
            x = 1 / 0
        except:
            send_error_args = client.handle_exception(dry_run=True)
        if not isinstance(send_error_args, dict):
            self.fail('Did not return dict from handle_exception with dry_run enabled.')


if __name__ == '__main__':
    unittest.main()
