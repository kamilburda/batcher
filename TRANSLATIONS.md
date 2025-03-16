# Providing Translations for Batcher

For easier usage, you may use a translation tool such as [Poedit](https://poedit.net).


## How do I translate the plug-in?

First, make sure you use the `batcher.pot` file for the latest version of the plug-in.
Use the .pot file in the `batcher/locale` folder (inside the folder with the installed plug-in), or, if in doubt, [download the latest version from GitHub](https://github.com/kamilburda/batcher/blob/main/batcher/locale/batcher.pot).


### Poedit

The following steps apply if you want to use Poedit.


#### Creating a New Translation

To create a new translation for your language:

1. Open Poedit, select `File → New from POT/PO file...` and select the `batcher/locale/batcher.pot` file.
2. Set the language of the translation.
3. Translate the strings (by filling in the `Translation` text field for each string).
4. If desired, go to `Translation → Properties...` and edit the translation file properties.
   If you do not do this, warning messages may pop up when saving, but they should be harmless.
5. When done, save your .po file.


#### Updating an Existing Translation

If you spotted some errors in your .po file or the plug-in was updated since the last translation was made, you may need to update the translation:

1. Open your .po file, select `Translation → Update from POT file...` and select the `batcher.pot` file for the latest plug-in version.
2. Update the translated strings.
   Make sure to check for:
   * new strings,
   * existing strings that were updated in the plug-in.
     Such strings may no longer be up-to-date and have a so-called "fuzzy" translation (and have a different color than other strings).
     Fuzzy strings that are not corrected will show up in the plug-in untranslated.


### Terminal

If you cannot/do not wish to use Poedit, you may use the terminal on Unix-based systems (Linux, macOS, etc.) or Windows Subsystem for Linux (WSL) on Windows.


#### Creating a New Translation

To create a new translation for your language:

1. Make sure that the `gettext` package is installed in your system.
   If not, install the `gettext` package.
   The command varies across Linux distributions, e.g. in Ubuntu you would type:
   
       sudo apt-get install gettext
   
2. Find the .pot file in the `batcher/locale` folder.
3. Open up terminal and run
   
       cd [folder where you extracted the package]/batcher/locale
       ./generate_po.sh [path to .pot file] [language]
   
   A .po file is generated in the same folder as the current working directory.
   
   `[language]` represents your language in the format `ll_CC`.
   `ll` is the language code and `CC` is the country code.
   For example, the French language is represented as `fr_FR`.
   If in doubt, you can consult the list of available language and country codes on the following pages:
   * [Usual Language Codes](https://www.gnu.org/software/gettext/manual/html_node/Usual-Language-Codes.html)
   * [Rare Language Codes](https://www.gnu.org/software/gettext/manual/html_node/Rare-Language-Codes.html)
   * [Country Codes](https://www.gnu.org/software/gettext/manual/html_node/Country-Codes.html)
   
4. Open the .po file in a text editor and translate each string in the `msgid` field to a string in the corresponding `msgstr` field.


#### Updating an Existing Translation

If you spotted some errors in the .po file or the plug-in is updated since the last translation was made, you may need to update the translation:

1. Run the following commands:
   
       cd [folder where you extracted the package]/batcher/locale
       ./update_po.sh [path to .po file] [path to .pot file]
   
   The old .po file is preserved and has the `.po.old` file extension.
   
2. Open the .po file in a text editor and update the translated strings.
   Make sure to check for:
   * new strings,
   * existing strings that were updated in the plug-in.
     Such strings may no longer be up-to-date and have a so-called "fuzzy" translation.
     Fuzzy strings are marked with a `, fuzzy` comment above them.
     Once you update the translated string, make sure to remove the `, fuzzy` comment, otherwise the string will show up untranslated in the plug-in.


## OK, I have finished the translation. What next?

You may want to test your translation first to make sure it works correctly, as described in the next section.

You may also want share your translation with the rest of the world. 😉
You can do so by submitting your translated .po file as follows:

1. Open a git pull request for the [plug-in repository](https://github.com/kamilburda/batcher).
2. Create a commit titled `Add [full language name] translation ([language])` (e.g. `Add French translation (fr_FR)`) that adds the translated .po file to the following path:
  
      [repository root]/batcher/locale/[language]/LC_MESSAGES/batcher.po
  
  If you are updating a translation, name your commit message `Update [full language name] translation ([language])` (e.g. `Update French translation (fr_FR)`).


## How can I test my translation?

First, make sure Batcher is installed in the folder for GIMP plug-ins.
You then need to generate an .mo file from the translated .po file.


### Generating .mo file

#### Poedit

Poedit automatically generates the .mo file when you save your .po file.
Move and rename the .mo file to

    [GIMP plug-ins folder]/batcher/locale/[language]/LC_MESSAGES/batcher.mo
   
where `[language]` is the language in which you translated the plug-in.
`[language]` is a part of the .po file, e.g. for a file named `fr_FR.po`, the language is `fr_FR`.

#### Terminal

Generate the .mo file as follows:
   
    cd [GIMP plug-ins folder]/batcher/locale
    ./generate_mo.sh [path to .po file] [language]


### Running GIMP

Now that the .mo file is renamed and placed in the proper folder, you can proceed to test your translation in GIMP.

#### Linux or macOS

Run GIMP from the terminal. If you use the official GIMP AppImage for Linux distributions or the macOS disk image, you can run GIMP with a specific language as follows:
    
    export LANG="[language].UTF-8"
    [path to GIMP AppImage/disk image]

If you use the Flatpak installation on Linux:

    export LANG="[language].UTF-8"
    flatpak run org.gimp.GIMP//stable


#### Windows

Run GIMP from the Windows command line as follows:
   
    set lang=[language].UTF-8
    gimp.exe

If Windows does not recognize the GIMP executable, specify the full path. For example, if GIMP 3.0 is installed using the official GIMP installer, the full path by default will be
    
    "C:\Program Files\GIMP 3\bin\gimp.exe"
