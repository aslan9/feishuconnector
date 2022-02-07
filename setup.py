#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages
from feishuconnector import __version__


setup(
    name='feishuconnector',
    version=__version__,
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
    install_requires=open('requirements.txt').readlines(),
)