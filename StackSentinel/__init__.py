"""
StackSentinel Python Client
===========================
Use this client to integrate StackSentinel (www.stacksentinel.com) into your Python projects. You can also use
platform-specific StackSentinel clients, such as the stacksentinel-flask client:

>>> import StackSentinel
>>> stack_sentinel_client = StackSentinel.StackSentinelClient(
...     account_token='-- YOUR ACCOUNT TOKEN --',
...     project_token='-- YOUR PROJECT TOKEN --',
...     environment='development-experiment', tags=['documentation-test'])
>>> print stack_sentinel_client
<StackSentinel.StackSentinelClient object at 0x10bcfbb90>
>>> try:
...     oops = 1 / 0
... except:
...     stack_sentinel_client.handle_exception()
...

That's all it takes. The information about the exception, along with platform and machine information, is gathered
up and sent to Stack Sentinel.

For WSGI applications, you can use the WSGI Middleware included with this project:

>>> app = StackSentinelMiddleware(app, stack_sentinel_client)

Compatibility
=============
This StackSentinel Python Client is compatible with Python 2.7 and 3.x and Stack Sentinel API v1.

License
=======
Copyright 2015 Stack Sentinel. All Rights Reserved.

This software is licensed under the Apache License, version 2.0.

See LICENSE for full details.

Getting Help
============
Email support@stacksentinel.com with your questions.
"""
import json
import os
import sys

#
# Some sandboxed environments do not have socket
try:
    import socket
except:
    socket = None

#
# Some sandboxed environments do not have platform
try:
    import platform
except:
    platform = None

#
# Python2/3
try:
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request, HTTPError


class StackSentinelError(ValueError):
    """
    Exception raised when there is an error communicating with backend or generating request for backend.
    """
    pass


class StackSentinelClient(object):
    """
    Client to send exceptions to StackSentinel. See in particular the handle_exception method, which can be called
    within an except block. See also the send_error method, which at a lower level generates an appropriate payload
    for the StackSentinel API.
    """
    USER_AGENT = 'STACK SENTINEL PYTHON CLIENT'

    def __init__(self, account_token, project_token, environment, tags=None,
                 endpoint="https://api.stacksentinel.com/api/v1/insert"):
        """

        :param account_token: Your account token, as supplied by StackSentinel
        :param project_token: Your project token, as supplied by StackSentinel
        :param environment: The environment of the project (eg, "production", "devel", etc)
        :param tags: Any tags you want associated with *all* errors sent using this client.
        :param endpoint: API endpoint. Defaults to StackSentinel backend.
        """
        self.account_token = account_token
        self.project_token = project_token
        self.endpoint = endpoint
        self.environment = environment
        if tags:
            self.tags = tags
        else:
            self.tags = []

    @staticmethod
    def _serialize_object(obj):
        """
        When the state of an exception includes something that we can't pickle, show something useful instead.
        """
        try:
            return repr(obj)
        except:
            return '<Cannot Be Serialized>'

    def handle_exception(self, exc_info=None, state=None, tags=None, return_feedback_urls=False,
                         dry_run=False):
        """
        Call this method from within a try/except clause to generate a call to Stack Sentinel.

        :param exc_info: Return value of sys.exc_info(). If you pass None, handle_exception will call sys.exc_info() itself
        :param state: Dictionary of state information associated with the error. This could be form data, cookie data, whatnot. NOTE: sys and machine are added to this dictionary if they are not already included.
        :param tags: Any string tags you want associated with the exception report.
        :param return_feedback_urls: If True, Stack Sentinel will return feedback URLs you can present to the user for extra debugging information.
        :param dry_run: If True, method will not actively send in error information to API. Instead, it will return a request object and payload. Used in unittests.

        """
        if not exc_info:
            exc_info = sys.exc_info()
        if exc_info is None:
            raise StackSentinelError("handle_exception called outside of exception handler")

        (etype, value, tb) = exc_info
        try:
            msg = value.args[0]
        except:
            msg = repr(value)

        if not isinstance(tags, list):
            tags = [tags]

        limit = None

        new_tb = []
        n = 0

        while tb is not None and (limit is None or n < limit):
            f = tb.tb_frame
            lineno = tb.tb_lineno
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            tb = tb.tb_next
            n = n + 1

            new_tb.append({'line': lineno, 'module': filename, 'method': name})

        if state is None:
            state = {}

        if 'sys' not in state:
            try:
                state['sys'] = self._get_sys_info()
            except Exception as e:
                state['sys'] = '<Unable to get sys: %r>' % e
        if 'machine' not in state:
            try:
                state['machine'] = self._get_machine_info()
            except Exception as e:
                state['machine'] = '<Unable to get machine: %e>' % e

        if tags is None:
            tags = []

        # The joy of Unicode
        if sys.version_info.major > 2:
            error_type = str(etype.__name__)
            error_message = str(value)
        else:
            error_type = unicode(etype.__name__)
            error_message = unicode(value)

        send_error_args = dict(error_type=error_type,
                               error_message=error_message,
                               traceback=new_tb,
                               environment=self.environment,
                               state=state,
                               tags=self.tags + tags,
                               return_feedback_urls=return_feedback_urls)
        if dry_run:
            return send_error_args
        else:
            self.send_error(**send_error_args)

    def _get_sys_info(self):
        sys_info = {
            'version': sys.version,
            'version_info': sys.version_info,
            'path': sys.path,
            'platform': sys.platform
        }
        return sys_info

    def _get_machine_info(self):
        machine = {}
        if socket:
            try:
                machine['hostname'] = socket.gethostname()
            except Exception as e:
                machine['hostname'] = '<Could not determine: %r>' % (e,)
        else:
            machine['hostname'] = "<socket module not available>"
        machine['environ'] = dict(os.environ)
        if platform:
            machine['platform'] = platform.uname()
            machine['node'] = platform.node()
            machine['libc_ver'] = platform.libc_ver()
            machine['version'] = platform.version()
            machine['dist'] = platform.dist()
        return machine

    def send_error(self, error_type, error_message, traceback, environment, state, tags=None,
                   return_feedback_urls=False):
        """
        Sends error payload to Stack Sentinel API, returning a parsed JSON response. (Parsed as in,
        converted into Python dict/list objects)

        :param error_type: Type of error generated. (Eg, "TypeError")
        :param error_message: Message of error generated (Eg, "cannot concatenate 'str' and 'int' objects")
        :param traceback: List of dictionaries. Each dictionary should contain, "line", "method", and "module" keys.
        :param environment: Environment the error occurred in (eg, "devel")_
        :param state: State of the application when the error happened. Could contain form data, cookies, etc.
        :param tags: Arbitrary tags you want associated with the error. list.
        :param return_feedback_urls: If True, return payload will offer URLs to send users to collect additional feedback for debugging.
        :return: Parsed return value from Stack Sentinel API
        """

        (request, payload) = self._generate_request(environment, error_message, error_type, return_feedback_urls,
                                                    state, tags, traceback)
        try:
            response = urlopen(request)
        except HTTPError as e:
            if e.code == 400:
                raise StackSentinelError(e.read())
            else:
                raise

        if sys.version_info.major > 2:
            text_response = response.read().decode(response.headers.get_content_charset() or 'utf8')
        else:
            encoding = response.headers.get('content-type', '').split('charset=')[-1].strip()
            if encoding:
                text_response = response.read().decode('utf8', 'replace')
            else:
                text_response = response.read().decode(encoding)

        return json.loads(text_response)

    def _generate_request(self, environment, error_message, error_type, return_feedback_urls, state, tags, traceback):
        payload = json.dumps(dict(
            account_token=self.account_token,
            project_token=self.project_token,
            return_feedback_urls=return_feedback_urls,
            errors=[dict(
                error_type=error_type,
                error_message=error_message,
                environment=environment,
                traceback=traceback,
                state=state,
                tags=tags or []
            )]
        ), default=self._serialize_object)
        request = Request(self.endpoint, data=payload.encode('utf8'), headers={
            'Accept-Charset': 'utf-8',
            "Content-Type": "application/x-www-form-urlencoded ; charset=UTF-8",
            'User-Agent': self.USER_AGENT})
        return (request, payload)


class StackSentinelMiddleware(object):
    """
    Stack Sentinel middleware client. As easy as this:

    >>> client = StackSentinelClient(...)
    >>> app = StackSentinelMiddleware(app, client)
    """
    def __init__(self, app, client):
        """
        :param app: WSGI application object
        :param client: Instance of StackSentinel
        """
        self.app = app

        self.client = client

    def __call__(self, environ, start_response):
        result = None

        try:
            result = self.app(environ, start_response)
        except Exception:
            self.client.handle_exception(state={'wsgi_environ': environ})
            raise

        try:
            if result is not None:
                for i in result:
                    yield i
        except Exception:
            self.client.handle_exception(state={'wsgi_environ': environ})
            raise

        finally:
            if hasattr(result, 'close'):
                result.close()
