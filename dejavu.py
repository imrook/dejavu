#!/usr/bin/python

import argparse
import json
import os
import subprocess
import sys
import warnings
from argparse import RawTextHelpFormatter

from dejavu import Dejavu
from dejavu.recognize import FileRecognizer

warnings.filterwarnings("ignore")

DEFAULT_CONFIG_FILE = "dejavu.cnf.SAMPLE"


def init(configpath):
    """ 
    Load config from a JSON file
    """
    try:
        with open(configpath) as f:
            config = json.load(f)
    except IOError as err:
        print('Cannot open configuration: %s. Exiting' % (str(err)))
        sys.exit(1)

    # create a Dejavu instance
    return Dejavu(config)


def print_clips(clips):
    print 'confidence'.rjust(10), 'start'.rjust(8), 'end'.rjust(8), 'source'
    for clip in clips:
        print clip['confidence'].rjust(10), clip['start'].rjust(8), clip['end'].rjust(8), clip['source']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Dejavu: Audio Fingerprinting library',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('-c', '--config', nargs='?',
                        help='Path to configuration file\n'
                             'Usages: \n'
                             '--config /path/to/config-file\n')
    parser.add_argument('-f', '--fingerprint', nargs='*',
                        help='Fingerprint files in a directory\n'
                             'Usages: \n'
                             '--fingerprint /path/to/directory extension\n'
                             '--fingerprint /path/to/directory')
    parser.add_argument('-r', '--recognize', nargs='*',
                        help='Recognize what is '
                             'playing through the microphone\n'
                             'Usage: \n'
                             '--recognize mic number_of_seconds \n'
                             '--recognize file path/to/file split_milliseconds start_milliseconds limit_milliseconds\n')
    args = parser.parse_args()

    if not args.fingerprint and not args.recognize:
        parser.print_help()
        sys.exit(0)

    config_file = args.config
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
        # print 'Using default config file: %s' % (config_file)

    djv = init(config_file)
    if args.fingerprint:
        # Fingerprint all files in a directory
        if len(args.fingerprint) == 2:
            directory = args.fingerprint[0]
            extension = args.fingerprint[1]
            print('Fingerprinting all .%s files in the %s directory'
                  % (extension, directory))
            djv.fingerprint_directory(directory, ['.' + extension], 4)

        elif len(args.fingerprint) == 1:
            filepath = args.fingerprint[0]
            if os.path.isdir(filepath):
                print('Please specify an extension if you\'d like to fingerprint a directory!')
                sys.exit(1)
            djv.fingerprint_file(filepath)

    elif args.recognize:
        # Recognize audio source
        songs = []
        opt_arg = args.recognize[0]
        try:
            split_milliseconds = int(args.recognize[1])
        except:
            split_milliseconds = 10000
        try:
            start_milliseconds = int(args.recognize[2])
        except:
            start_milliseconds = 0
        try:
            limit_milliseconds = int(args.recognize[3])
        except:
            limit_milliseconds = None

        songs = FileRecognizer(djv).recognize(opt_arg, split_milliseconds, start_milliseconds, limit_milliseconds)

        subprocess.check_output('rm -f results/out*', shell=True)

        # use debug to add original clips between found clips. NOTE: assumes source is also video
        debug = True
        clip_infos = []
        clip_duration = split_milliseconds / 1000.0
        i = 0

        # reverse the list if debugging so your ears won't get distracted by sequential clips
        if debug:
            songs = list(reversed(songs))

        for i, song in enumerate(songs):

            target_start = float(song['offset_seconds'])
            target_end = target_start + clip_duration

            if i == len(songs) - 1:  # last
                target_end -= ((split_milliseconds - limit_milliseconds % split_milliseconds) / 1000.0)
                if (target_end - start_milliseconds) < .01:
                    continue

            if debug:
                debug_start = float((start_milliseconds + (len(songs) - 1 - i) * split_milliseconds) / 1000.0)
                clip_infos.append({
                    'out': 'results/out%s.mp4' % (i * 2),
                    'source': opt_arg,
                    'start': "%.2f" % debug_start,
                    'end': "%.2f" % (debug_start + clip_duration),
                    'confidence': 'Source'
                })

            if debug:
                target_out_file_name = 'results/out%s.mp4' % (i * 2 + 1)
            else:
                target_out_file_name = 'results/out%s.mp4' % i

            clip_infos.append({
                'out': target_out_file_name,
                'source': 'mp3/%s.mp4' % song['song_name'],
                'start': "%.2f" % target_start,
                'end': "%.2f" % target_end,
                'confidence': str(song['confidence'])
            })

        print_clips(clip_infos)

        inputs = ''
        input_mapping = ''

        for i, clip_info in enumerate(clip_infos):
            subprocess.check_output([
                'ffmpeg', '-y',
                '-i', clip_info['source'],
                '-ss', clip_info['start'],
                '-to', clip_info['end'],
                '-c:a', 'aac',
                '-strict', 'experimental',
                clip_info['out']
            ])

            inputs += '[%d:v:0][%d:a:0]' % (i, i)
            input_mapping += '-i %s ' % clip_info['out']

        inputs += 'concat=n=%d' % len(clip_infos)
        merge_cmd = 'ffmpeg -y ' + input_mapping + '-filter_complex "' + inputs + ':v=1:a=1[outv][outa]" ' + \
                    '-map "[outv]" -map "[outa]" output.mp4'
        subprocess.check_output(merge_cmd, shell=True)

        print_clips(clip_infos)
