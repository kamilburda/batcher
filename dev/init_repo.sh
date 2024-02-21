#!/bin/bash

# This script initializes the Batcher git repository.

orig_cwd="$(pwd)"

# Install required programs/packages
# If supported package managers are not available (apt-get), developer has to
# install missing packages manually.

function command_exists()
{
  command -v "$1" > /dev/null 2>&1
  return $?
}

if command_exists 'apt-get'; then
  required_packages='git
ruby
ruby-dev
build-essential
patch
zlib1g-dev
liblzma-dev
libgmp-dev
libffi-dev
gcc
gettext
python3
python3-pip
gimp'

  sudo apt-get install -y $required_packages
else
  required_packages='git
ruby
python3
python3-pip
gettext
gimp'

  echo 'Make sure the following packages are installed:'
  echo "$required_packages"
  echo ''
  echo -n "If you have all required packages installed, press 'y', otherwise press any key to terminate the script and install the packages manually: "
  read -n 1 key_pressed
  
  echo ''
  
  if [ "${key_pressed,,}" != 'y' ]; then
    echo "Terminating script. Please install packages listed above before running the script." 1>&2
    exit 1
  fi
fi


# Installation of Ruby and Python packages

sudo gem install bundler

python_modules='pathspec
requests
parameterized
psutil
pyyaml
GitPython'

sudo pip install $python_modules


# GIMP initialization

required_version='2.99.18'
gimp_version="$(gimp --version | sed 's/.*version \([0-9][0-9]*.[0-9][0-9]*.[0-9][0-9]*\)$/\1/')"

if [[ "$gimp_version" == "$required_version" ]]; then
  gimp_version_major_minor="${gimp_version%.*}"
  gimp_local_dirpath="$HOME"'/.config/GIMP/'"$gimp_version_major_minor"
else
  echo "Unsupported version of GIMP ($gimp_version). Please install GIMP version $required_version."
  exit 1
fi

plugin_main_repo_dirname='batcher'
plugin_page_branch_name='gh-pages'
repo_url='https://github.com/kamilburda/batcher.git'
repo_dirpath="$gimp_local_dirpath"'/'"$plugin_main_repo_dirname"

gimprc_filename='gimprc'
gimprc_filepath="$gimp_local_dirpath"'/'"$gimprc_filename"

if [ ! -f "$gimprc_filepath" ]; then
  echo "$gimprc_filename"' does not exist, running GIMP...'

  get_procedure="procedure = Gimp.get_pdb().lookup_procedure('gimp-quit')"
  set_config="config = procedure.create_config(); config.set_property('force', True)"
  run_procedure='procedure.run(config)'

  gimp --no-interface --new-instance --batch-interpreter='python-fu-eval' \
    --batch "${get_procedure}; ${set_config}; ${run_procedure}"
fi

if [ ! -f "$gimprc_filepath" ]; then
  echo 'Warning: "'"$gimprc_filepath"'" could not be found or created.'
  echo 'Manually run GIMP and add the repository path "'"$repo_dirpath"'" to the list of plug-in folders (Edit -> Preferences -> Folders -> Plug-Ins).'
fi


# Repository initialization

echo 'Cloning main branch of '"$repo_url"' into '\'"$repo_dirpath"\'
git clone --recurse-submodules -- "$repo_url" "$repo_dirpath"

cd "$repo_dirpath"

echo 'Setting up git hooks'
ln -s 'dev/git_hooks/commit_msg.py' '.git/hooks/commit-msg'
ln -s 'dev/git_hooks/pre_commit.py' '.git/hooks/pre-commit'

echo 'Enabling core.autocrlf in git config'
git config --local 'core.autocrlf' 'true'

cd 'docs'

echo 'Cloning '"$plugin_page_branch_name"' branch of '"$repo_url"' into '\'"$repo_dirpath"'/docs/'"$plugin_page_branch_name"\'
git clone --branch "$plugin_page_branch_name" -- "$repo_url" "$plugin_page_branch_name"

cd "$plugin_page_branch_name"

echo 'Setting up git hooks for branch '"$plugin_page_branch_name"
ln -s "$repo_dirpath"'/dev/git_hooks/commit_msg.py' '.git/hooks/commit-msg'

echo 'Enabling core.autocrlf in git config for branch '"$plugin_page_branch_name"
git config --local 'core.autocrlf' 'true'

bundle install

cd "$orig_cwd"
