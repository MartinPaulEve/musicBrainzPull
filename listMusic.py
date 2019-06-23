"""Music release generator.

Usage:
  listMusic.py gen <id_file> <template_file> <output_file> [--debug] [--refresh]
  listMusic.py cv <id_file> <output_file> [--debug] [--refresh]
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

"""
import musicbrainzngs
import os
from docopt import docopt
import logging
import pygogo as gogo

app = "Music Release Generator 1.1"

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)

logger = gogo.Gogo(
    'Music Release Generator',
    low_formatter=formatter,
    high_formatter=formatter,
    monolog=True).logger


def load_ids(args):
    id_list = []

    # load the ID file
    logger.debug('Loading ID file')

    try:
        with open(args["<id_file>"], "r") as id_file:
            ids = id_file.readlines()

            for id_full in ids:

                release_id = id_full.split(":")

                if not len(release_id) == 3:
                    logger.error("ID line {0} is malformed".format(id_full))
                    logger.info('Shutting down')
                    return False

                id_list.append(release_id[0])

                # fetch release
                logger.debug("Fetching release {0}".format(release_id[0]))
                if not fetch_release(release_id, args["--refresh"]):
                    return False

                # fetch cover
                logger.debug("Fetching cover art for {0}".format(release_id[0]))
                if not fetch_cover(release_id, args["--refresh"]):
                    return False

    except EnvironmentError:
        logger.error('Cannot open ID file')
        logger.info('Shutting down')
        return False

    return id_list

def cv_mode():
    pass


def main(args):
    if '--debug' in args and args['--debug']:
        logger.setLevel('DEBUG')
    else:
        logger.setLevel('INFO')

    logger.debug(app)

    logger.debug('Setting MB useragent')
    musicbrainzngs.set_useragent('martinevereleases', '1.1')

    id_list = load_ids(args)

    if not id_list:
        return

    if 'cv' in args and args['cv']:
        logger.debug('Working in CV mode (for https://github.com/MartinPaulEve/eprintsToCV)')

        logger.debug("Building output HTML")
        template = generate_cv_html(id_list)
    else:
        # load the template
        logger.debug('Loading template file')

        try:
            with open(args["<template_file>"], "r") as template_file:
                template = template_file.read()
        except EnvironmentError:
            logger.error('Cannot open template file')
            logger.info('Shutting down')
            return

        # now build the HTML
        logger.debug("Building output HTML")
        output_html = generate_html(id_list)

        # replace the output template
        logger.debug("Substituting contents in template")
        template = template.replace('[CONTENTS]', output_html)

    # write to a file
    logger.debug("Writing output")
    try:
        with open(args["<output_file>"], "w") as out_file:
            out_file.write(template)
    except EnvironmentError:
        logger.error('Cannot open output file: {0}'.format(args["<output_file>"]))
        logger.info('Shutting down')
        return

    logger.debug("Done")


def generate_cv_html(id_list):
    output_html = '<div class="section" id="music"><h2 class="sectionheader">MUSIC</h2>'

    the_date = ''

    template_new_date = '<p class="anitemnewdate genericitem"><span class="prefix bold">[[DATE]]</span><span class="bibitem">[[CONTENTS]]</span></p>'
    template = '<p class="anitem genericitem"><span class="prefix bold">&nbsp;</span><span class="bibitem">[[CONTENTS]]</span></p>'

    for release_id in id_list:
        try:
            with open("{0}.data".format(release_id), "r") as in_file:
                fields = in_file.read().split("\n")

                artist = fields[0]
                release_name = fields[1]
                url = fields[6]
                year = fields[2].split('-')[0]
                label = fields[3]

                if fields[5] == 'remix':
                    remix = ' (remix)'
                else:
                    remix = ''

                contents = '<a href="https://{3}">{0} - {1}{2}{4}</a>'.format(artist, release_name, remix, url,
                                                                              ' (' + label + ')' if label != '' else '')

                if year != the_date:
                    new_output_html = template_new_date.replace('[[DATE]]', year).replace('[[CONTENTS]]', contents)
                    the_date = year
                else:
                    new_output_html = template.replace('[[CONTENTS]]', contents)

                output_html += new_output_html
        except EnvironmentError:
            logger.error('Cannot write data file for {0}'.format(release_id))
            logger.info('Shutting down')
            return False

    output_html += '</div>'

    return output_html


def generate_html(id_list):
    first_td = ['', '']
    second_td = ['', '']
    td_first = ''
    td_second = ''
    output_html = ''
    for release_id in id_list:
        try:
            with open("{0}.data".format(release_id), "r") as in_file:
                fields = in_file.read().split("\n")

                artist = fields[0]
                release_name = fields[1]
                url = fields[6]
                year = fields[2].split('-')[0]
                label = fields[3]

                if fields[5] == 'remix':
                    remix = ' (remix)'
                else:
                    remix = ''

                td_first = '<td><a href="https://{0}"><img src="{1}" alt="{2} - {3}" ' \
                           'style="width:150px;max-width:150px;"></img></a></td>'.format(url, release_id, artist,
                                                                                         release_name)

                td_second = '<td style="padding-bottom: 15px;"><a href="https://{0}">{1} - {2}{5}</a>' \
                            '<br/>({3}{6}{4})</td>'.format(url, artist, release_name, label, year, remix,
                                                            ', ' if label != "" else '')

                new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
                output_html += new_output_html
        except EnvironmentError:
            logger.error('Cannot write data file for {0}'.format(release_id))
            logger.info('Shutting down')
            return False

    # at this point, we need to check whether to write the final line
    if first_td[0] == '':
        # do nothing
        pass
    elif first_td[1] == '':
        # one is loaded, the other empty
        logger.debug("Building last blank entry")
        td_first = '<td></td>'
        td_second = '<td style="padding-bottom: 15px;"></td>'
        new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
        output_html += new_output_html
    else:
        # both loaded
        new_output_html, first_td, second_td = process_arrays(first_td, second_td, td_first, td_second)
        output_html += new_output_html
    return output_html


def fetch_cover(release_id, refresh=False):
    if not os.path.isfile(release_id[0]) or refresh:
        logger.debug("Hard refreshing cover art for {0}".format(release_id[0]))
        try:
            data = musicbrainzngs.get_image_front(release_id[0])
        except musicbrainzngs.WebServiceError as exc:
            logger.error("Error fetching cover art for {0}".format(release_id[0]))
            logger.error(exc)
            logger.info('Shutting down')
            return False

        try:
            with open(release_id[0], "wb") as out_file:
                out_file.write(data)
        except EnvironmentError:
            logger.error('Cannot write cover art for {0} to file'.format(release_id[0]))
            logger.info('Shutting down')
            return False
    else:
        logger.debug("Using pre-fetched cover art for {0}".format(release_id[0]))

    return True


def fetch_release(release_id, refresh=False):
    if not os.path.isfile("{0}.data".format(release_id[0])) or refresh:
        logger.debug("Hard refreshing data for {0}".format(release_id[0]))
        try:
            release = musicbrainzngs.get_release_by_id(release_id[0], includes=["artists", "labels"])['release']
        except musicbrainzngs.WebServiceError as exc:
            logger.error("Error fetching data for {0}".format(release_id[0]))
            logger.error(exc)
            logger.info('Shutting down')
            return False

        try:
            with open("{0}.data".format(release_id[0]), "w") as out_file:
                artist = release["artist-credit"][0]["artist"]
                try:
                    label = release["label-info-list"][0]["label"]["name"]
                    catno = release["label-info-list"][0]["catalog-number"]
                except IndexError:
                    label = ''
                    catno = ''

                out_file.writelines('\n'.join(
                    [artist["name"], release["title"], release["date"], label, catno, release_id[1], release_id[2]]))
        except EnvironmentError:
            logger.error('Cannot write data for {0} to file'.format(release_id[0]))
            logger.info('Shutting down')
            return False
    else:
        logger.debug("Using pre-fetched data for {0}".format(release_id[0]))

    return True


def process_arrays(first_td, second_td, td_first, td_second):
    output_html = ""
    if first_td[0] == '':
        logger.debug("Loading to first TD")
        first_td[0] = td_first
    elif first_td[1] == '':
        logger.debug("Loading to second TD")
        first_td[1] = td_first

    if second_td[0] == '':
        second_td[0] = td_second
    elif second_td[1] == '':
        logger.debug("Array is loaded so building and emptying")
        second_td[1] = td_second
        # the array is loaded so append the output
        tr_first = "<tr>{0}{1}</tr>".format(first_td[0], first_td[1])
        tr_second = "<tr>{0}{1}</tr>".format(second_td[0], second_td[1])

        output_html += tr_first
        output_html += tr_second

        # unload the arrays
        first_td = ['', '']
        second_td = ['', '']

    return output_html, first_td, second_td


if __name__ == "__main__":
    arguments = docopt(__doc__, version=app)
    main(arguments)
