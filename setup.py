#!/usr/bin/env python

# https://setuptools.readthedocs.io/en/latest/setuptools.html


from setuptools import find_packages
from setuptools import setup


setup(name="git-replay",
      version="0.1",
      description="Prototype utility to track a change in git",
      author="Carl Baldwin",
      author_email="carl@ecbaldwin.net",
      url="https://github.com/ecbaldwin/git-replay",
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'git-graph = git_replay.graph_repo:main',
              'git-replay = git_replay.main:main',
              'post-rewrite = git_replay.post_rewrite:main',
              'post-receive = git_replay.post_receive:main',
              'update = git_replay.update:main',
          ]
      })
