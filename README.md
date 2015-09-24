# StackSentinel Python Client

Welcome to the Stack Sentinel Python client, which makes it super-duper easy to integrate
[Stack Sentinel](https://www.stacksentinel.com/) exception tracking into your Python project.

To get started tracking errors,

1. Create an account on StackSentinel.com
2. Create a new project
3. Get your PROJECT and API tokens
4. Add StackSentinel to your WSGI Middleware, or use it directly.

## Installation
stacksentinel is in pypi:

    # easy_install stacksentinel
    
or

    # pip install stacksentinel

## Directly use the client

Here's how to get started:

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
    
Then you can use the WSGI Middleware:
    
    >>> app = StackSentinelMiddleware(app, stack_sentinel_client)

# Compatibility
This StackSentinel Python Client is compatible with Python 2.7 and 3.x and Stack Sentinel API v1.

# License
Copyright 2015 Stack Sentinel. All Rights Reserved.

This software is licensed under the Apache License, version 2.0.

See LICENSE for full details.

# Getting Help
Email support@stacksentinel.com with your questions. 
