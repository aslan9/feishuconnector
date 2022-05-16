#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages

with open('feishuconnector/_version.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split("'")[1]

setup(
    name='feishuconnector',
    version=version,
    description=(
        'connect feishu content franchise'
    ),
    long_description=open('README.rst').read(),
    author='Changhao Jiang',
    author_email='jch@puyuan.tech',
    url='http://www.puyuan.tech',
    license='MIT License',
    packages=find_packages(),
    platforms=["all"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'requests >= 2.26.0',
        'numpy >= 1.21.2',
        'pandas >= 1.3.3',
        'requests-toolbelt >= 0.9.1',
        'dataframe-image-cn >= 0.1.1',
    ],
)
