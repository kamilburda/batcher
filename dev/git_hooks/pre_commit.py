#!/usr/bin/env python3

"""Git hook for updating and staging of end-user documentation files when "raw"
documentation files have been changed.
"""

import inspect
import os
import sys

import git

GIT_HOOKS_DIRPATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
ROOT_DIRPATH = os.path.dirname(os.path.dirname(GIT_HOOKS_DIRPATH))

sys.path.append(ROOT_DIRPATH)

from dev import sync_docs


def get_synced_files_to_stage(staged_filepaths, filepaths_to_sync):
  return [
    filepaths_to_sync[staged_filepath]
    for staged_filepath in staged_filepaths if staged_filepath in filepaths_to_sync]


def filepath_matches_gitignore(repo, filepath):
  try:
    repo.git.check_ignore(filepath)
  except git.exc.GitCommandError:
    return False
  else:
    return True


def main():
  repo = git.Repo(ROOT_DIRPATH)
  
  staged_filepaths = [
    os.path.normpath(os.path.join(ROOT_DIRPATH, diff.a_path))
    for diff in repo.index.diff('HEAD')]
  
  filepaths_to_sync = sync_docs.get_filepaths(sync_docs.PATHS_TO_PREPROCESS_FILEPATH)
  filepaths_to_sync.extend(sync_docs.get_filepaths(sync_docs.PATHS_TO_COPY_FILEPATH))
  
  sync_docs.main()
  
  synced_filepaths_to_stage = (
    get_synced_files_to_stage(staged_filepaths, filepaths_to_sync))
  
  filtered_synced_filepaths_to_stage = [
    filepath for filepath in synced_filepaths_to_stage
    if not filepath_matches_gitignore(repo, filepath)]
  
  repo.git.add(filtered_synced_filepaths_to_stage)


if __name__ == '__main__':
  main()
