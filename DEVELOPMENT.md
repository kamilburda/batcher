# Developing Batcher

* [Development Setup](#Development-Setup)
* [Creating a Release](#Creating-a-Release)
* [Coding Conventions](#Coding-Conventions)
* [Writing Commit Messages](#Writing-Commit-Messages)
* [Writing Documentation](#Writing-Documentation)


## Glossary

* Element = module, class, function or variable
* PDB = GIMP procedural database


## Development Setup <a name="Development-Setup"></a>

This section explains how to set up development environment for Batcher.

If you are using a Linux-based environment, the easiest to get set up is to download and run the [bash script](utils/init_repo.sh) that automatically installs any required dependencies and sets up the environment.
Users of Windows 10 and above may use e.g. the [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) to run the script.

If you cannot run the script, perform manual setup as per the instructions below.


### Setting up Repositories

Locate the directory for local GIMP plug-ins (e.g. `[home directory]/.config/GIMP/[version]` on Linux-based systems) and create a directory named `batcher`.

To make GIMP recognize the new directory as a directory containing the development version of Batcher, open GIMP, go to `Edit → Preferences → Folders → Plug-ins` and add the new directory to the list.
GIMP needs to be restarted for changes to take effect.

Clone the `gh-pages` branch (acting as the [GitHub page for Batcher](https://kamilburda.github.io/batcher/)) to `[Batcher directory]/docs/gh-pages`.
Several scripts depend on this directory location.

Some scripts require that the GitHub page be run locally.
To set up GitHub page locally:
* Install Ruby language.
* Install `bundler` gem:

      gem install bundler

* Switch to the `gh-pages` directory:

      cd docs/gh-pages
    
* Run `bundle` to install required dependencies:

      bundle install


### Git Hooks <a name="Git-Hooks"></a>

Set up git hooks located in `git_hooks` by creating symbolic links:

    ln -s git_hooks/commig_msg.py .git/hooks/commit-msg
    ln -s git_hooks/pre_commit.py .git/hooks/pre-commit

The `commit-msg` hook enforces several [conventions for commit messages](#Writing-Commit-Messages).

The `pre-commit` hook automatically propagates changes in files in `docs` to files comprising the end user documentation, such as the Readme and GitHub pages (located in `docs/gh-pages`).
See [User Documentation](#User-Documentation) for more information.


## Creating a Release <a name="Creating-a-Release"></a>

Run `utils/make_installers.sh` to create installer(s).
Use the `-i` option to specify platform(s) for which to create installers.
The installers will be created in the `installers/output` directory.


## Coding Conventions <a name="Coding-Conventions"></a>

For Python modules, follow PEP 8 conventions unless specified otherwise below.


### Line length

The maximum line length is:
* 100 characters for code,
* 80 characters for docstrings and comments.


### Indentation

Use two spaces for indentation.

Use hanging indents, with indented lines having two extra spaces.

For multi-line lists of variables (or arguments in function calls or definitions):
* if the variables fit in one line, use one line for all variables,
* if the variables do not fit in one line, use one line for each variable.

For multi-line conditions, align expressions vertically.

For multi-line function or class definitions, loops and `with` statements, use hanging indents and add two spaces after the beginning of the name of the function/class, first loop variable or the expression after the `with` keyword.
Example:

    def __init__(
          self,
          default_value,
          error_messages=None):
      with open(
             '/totally/ridiculously/long/path/to/file.txt', 'w') as f:
        pass


### Quotes in and Around Strings

Use single quotes except for cases when double quotes must be used.

Use double quotes:
* for docstrings,
* for emphasizing text in docstrings or comments,
* for string literals containing single quotes (to avoid inserting backslashes), e.g. `"the plug-in's interactive dialog"`

In comments and docstrings, wrap element names in backquotes.
Format function and method names as `function()`, i.e. with the trailing `()`.


### Naming

Use the following conventions for terms and variables:

| Term           | Variable name | Meaning                             |
|----------------|---------------|-------------------------------------|
| File name      | `filename`    | File basename                       |
| Directory name | `dirname`     | Directory basename                  |
| File path      | `filepath`    | Absolute or relative file path      |
| Directory path | `dirpath`     | Absolute or relative directory path |


### Imports

Import modules at the beginning of a module.

Avoid importing individual objects, classes or functions.
Notable exceptions:
* `pdb` object in `pygimplib`

Do not use wildcard imports.
Exceptions:
* internal modules whose public elements should be used directly through a package.
  These modules must define `__all__` to list all public elements to be imported.

Append `_` to imported modules with common names (e.g. `settings` becomes `settings_`) to avoid clashes with variable names.


### Module- and class-level code

Do not call code directly on the module or class level.
Exceptions to this rule include:
* initializing variables or constants,
* initializing application configuration,
* initializing a package or a library,
* standalone scripts such as test runners or git hooks.

Avoid calling functions from the GIMP API and GTK API on the module or class level.
These APIs are not fully initialized during GIMP startup and may result in plug-in procedures failing to be registered by GIMP.
Some functions such as `Gimp.directory()` as safe to call on the module or class level, but functions manipulating images will yield errors.


#### Main script function

For standalone scripts (such as utility scripts for creating a new release), the code inside `if __name__ == "__main__":` must be enclosed in a single function in order to avoid introducing global variables.
The name of the enclosing function should be `main()`.

Yes:
    
    def main():
      # code
    
    if __name__ == "__main__":
      main()

No:
    
    if __name__ == "__main__":
      # code


### Classes

Mixins can access and modify only those attributes defined in it.

No other classes may directly modify attributes defined in mixins.


### Methods

Use `@classmethod` for methods using class variables only.
Use `@staticmethod` for methods not using instance or class variables and logically belonging to the class.

Do not use `keys()` when iterating over dictionary keys.
Exceptions:
* improving clarity (e.g. when passing keys as a parameter to a function),
* iterating over objects of unhashable types (e.g. `gimp.Layer`).


### Unicode

Use Unicode strings internally.

Encode/decode Unicode strings when accessing the following external libraries:
* GIMP - use UTF-8 encoding.
  Encoding applies to:
  * `PDB_STRING*` parameters to PDB procedures,
  * accessing PDB procedures via `pdb.__getitem__` when passing a procedure name,
  * functions and object attributes provided by Python GIMP API.


### GTK, GObject

Always use `GObject` types (for `gtk.TreeView` columns, `__gsignals__`, etc.) instead of Python types if such `GObject` types exist.
For example, use `GObject.TYPE_STRING` instead of `str` for `Gtk.TreeView` columns of string type.

If it is necessary to get the dimensions or the relative position of a widget not yet realized, connect to the `"size-allocate"` signal and continue processing in the connected event handler.
Do not use `Gtk.main_iteration()` (which forces the GUI to update) for this purpose as it introduces flickering in the GUI.


## Writing Commit Messages <a name="Writing-Commit-Messages"></a>

This section explains how to write good commit messages.
The conventions are based on the following guidelines:
* [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
* [Git commit message](https://github.com/joelparkerhenderson/git_commit_message)

Some conventions are automatically enforced by the git hook [`commit-msg`](#Git-Hooks).
These conventions are marked by a trailing "*".


### General

* Each commit should change one and one thing only.
  For example, a bug fix and refactoring a function result in separate commits.
* Create separate commits for modifying a subtree/submodule and the parent repository.


### Formatting

Use the following format for commit messages*:

    <scope>: <header>
    
    <body>

* Limit the first line to 80 characters*. Strive for brevity and clarity.
* Do not end the first line with a period*.
* Begin the header with a verb in the imperative.
* Begin the header with a capital letter*.
* Be concise. Limit the message to the first line unless further explanation is required.
* Wrap the message body in 72 characters*.
* Wrap element names with backquotes.
* Format function and method names as `function()`.


#### Scope

Scope in the first line is optional, but highly recommended.

Use one of the following types of scope (ordered from the most preferred):
* subtree/submodule name
* package name
* module name
* filename without extension

To indicate a more detailed scope, use `.`, e.g. `gui.settings: ...`.


#### Verbs

The usage of leading verbs in the message header are not restricted, except for the following verbs, which should only be used in specific circumstances:
* Fix - bug fixes
* Correct - corrections of typos, grammar errors


## Writing Documentation <a name="Writing-Documentation"></a>

### API Documentation

Documentation to modules, classes and functions are written as docstrings directly in the source code.

Each module except test modules should contain a short module-level docstring.
This docstring should be placed at the top of the module (after `#!/usr/bin/env python3` if present), followed by one empty blank line.


### User Documentation <a name="User-Documentation"></a>

To update documentation for end users, modify the "raw" documentation - files located in `docs` (except files in `gh-pages`).
Do not modify other documentation files outside `docs` as they are automatically updated by [git hooks](#Git-Hooks) when committing changes to the files in `docs`.

Any changes in user documentation propagated to files in `docs/gh-pages` should be reviewed first before pushing to the `gh-pages` branch.

In Markdown files, break lines on sentences.
For long sentences, rely on soft wrap or split them into multiple shorter sentences.
