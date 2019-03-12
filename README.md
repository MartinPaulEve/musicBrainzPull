#musicBrainzPull
This application can generate a list of releases using MusicBrainz data. An example of its output can be found at https://eve.gd/music/ .

##Installation
First, clone the repo to your local machine. Then install the requirements into a virtual environment using pip -r requirements.txt.

##Usage
```
Usage:
  listMusic.py <id_file> <template_file> <output_file> [--debug] [--refresh]
  listMusic.py (-h | --help)
  listMusic.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --debug       Enable debug output.
  --refresh     Delete cached versions and do a hard refresh from MusicBrainz.

Info:

The ID file specified should have a colon-delimited list of MusicBrainz release IDs, whether the release is a remix,
and a URL.

An example list might look like this:
3ba21ea2-3ff4-41b6-991e-6bd4d26ab223:remix:musicbrainz.org/release/3ba21ea2-3ff4-41b6-991e-6bd4d26ab223
d6c0d742-e4a3-4b1c-b9be-abf5d703adf9:original:www.junodownload.com/products/course-correction-ep/3775354-02/

Note that no field should contain a colon (":").

The template file should have a block of text "[CONTENTS]" within a table.
```