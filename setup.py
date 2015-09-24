from setuptools import setup, find_packages

version = '1.1'
url = 'https://github.com/StackSentinel/stacksentinel-python'

setup(
    name='stacksentinel',
    description='Stack Sentinel client and WSGI middleware',
    keywords='stack sentinel stacksentinel exception tracking api',
    version=version,
    author="Jeri MgCuckin",
    author_email="jerymcguckin@stacksentinel.com",
    url=url,
    test_suite='tests',
    packages=find_packages(exclude=['tests']),
    classifiers=["Programming Language :: Python",
                 "Programming Language :: Python :: 2",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.4"
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Intended Audience :: Developers',
                 ],
    license='Apache License (2.0)'
)
