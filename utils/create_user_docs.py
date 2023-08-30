#!/usr/bin/env python3

"""Generating user documentation from GitHub Pages files."""
import os
import shutil
import sys

import psutil
import requests
import yaml

from batcher import pygimplib as pg

from utils import process_local_docs


MODULE_DIRPATH = os.path.abspath(os.path.dirname(pg.utils.get_current_module_filepath()))

FILE_ENCODING = 'utf-8'

PAGE_CONFIG_FILENAME = '_config.yml'
SITE_DIRNAME = '_site'
JEKYLL_SERVER_LOCALHOST_IP = '127.0.0.1'
JEKYLL_SERVER_PORT = '4000'


def main(github_page_dirpath, output_dirpath):
  run_github_page_locally(github_page_dirpath)
  _process_local_docs(github_page_dirpath, output_dirpath)


def run_github_page_locally(github_page_dirpath):
  run_github_page_locally_process = psutil.Popen(
    [os.path.join(MODULE_DIRPATH, 'run_github_page_locally.sh'), '--release'])
  
  page_config_filepath = os.path.join(github_page_dirpath, PAGE_CONFIG_FILENAME)
  
  with open(page_config_filepath, 'r', encoding=FILE_ENCODING) as f:
    page_config = yaml.load(f.read())
  
  page_ready = False
  
  while not page_ready:
    try:
      requests.get(
        'http://{}:{}{}/'.format(
          JEKYLL_SERVER_LOCALHOST_IP, JEKYLL_SERVER_PORT, page_config['baseurl']))
    except requests.ConnectionError:
      pass
    else:
      page_ready = True
  
  for child in run_github_page_locally_process.children(recursive=True):
    child.kill()
  
  run_github_page_locally_process.kill()


def _process_local_docs(github_page_dirpath, output_dirpath):
  copy_directory(os.path.join(github_page_dirpath, SITE_DIRNAME), output_dirpath)
  
  process_local_docs.main(
    output_dirpath,
    os.path.join(github_page_dirpath, PAGE_CONFIG_FILENAME))


def copy_directory(source_dirpath, dest_dirpath):
  for name in os.listdir(source_dirpath):
    if os.path.isdir(os.path.join(source_dirpath, name)):
      shutil.copytree(
        os.path.join(source_dirpath, name),
        os.path.join(dest_dirpath, name))
    else:
      shutil.copy2(
        os.path.join(source_dirpath, name),
        os.path.join(dest_dirpath, name))


if __name__ == '__main__':
  github_page_absolute_dirpath = os.path.abspath(sys.argv[1])
  output_absolute_dirpath = os.path.abspath(sys.argv[2])
  
  main(github_page_absolute_dirpath, output_absolute_dirpath)
