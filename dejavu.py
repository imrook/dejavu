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
from dejavu.recognize import MicrophoneRecognizer

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
        print("Cannot open configuration: %s. Exiting" % (str(err)))
        sys.exit(1)

    # create a Dejavu instance
    return Dejavu(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Dejavu: Audio Fingerprinting library",
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
                             '--recognize file path/to/file split_milliseconds start_milliseconds limit_milliseconds \n')
    args = parser.parse_args()

    if not args.fingerprint and not args.recognize:
        parser.print_help()
        sys.exit(0)

    config_file = args.config
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
        # print "Using default config file: %s" % (config_file)

    djv = init(config_file)
    if args.fingerprint:
        # Fingerprint all files in a directory
        if len(args.fingerprint) == 2:
            directory = args.fingerprint[0]
            extension = args.fingerprint[1]
            print("Fingerprinting all .%s files in the %s directory"
                  % (extension, directory))
            djv.fingerprint_directory(directory, ["." + extension], 4)

        elif len(args.fingerprint) == 1:
            filepath = args.fingerprint[0]
            if os.path.isdir(filepath):
                print("Please specify an extension if you'd like to fingerprint a directory!")
                sys.exit(1)
            djv.fingerprint_file(filepath)

    elif args.recognize:
        # Recognize audio source
        songs = []
        source = args.recognize[0]
        opt_arg = args.recognize[1]
        try:
            split_milliseconds = args.recognize[2]
            opt_arg3 = args.recognize[3]
            opt_arg4 = args.recognize[4]
        except:
            pass

        if source in ('mic', 'microphone'):
            songs = djv.recognize(MicrophoneRecognizer, limit_milliseconds=int(opt_arg))
        elif source == 'file':
            start_milliseconds = int(opt_arg3)
            songs = djv.recognize(FileRecognizer, filename=opt_arg, split_milliseconds=int(split_milliseconds),
                                  start_milliseconds=start_milliseconds, limit_milliseconds=int(opt_arg4))

        # subprocess.check_output([
        #     "ffmpeg", "-y",
        #     "-ss", "15",
        #     '-t', "10",
        #     '-c:a', 'aac',
        #     '-strict', 'experimental',
        #     "-i", "mp3/MC-Hamer--U-Cant-Touch-This.3gp",
        #     'results/in.mp4'])
        subprocess.check_output("rm -f results/out*", shell=True)

        i = 0
        for song in songs:
            if song is not None:
                test_file_name = "results/out%s.mp4" % i
                subprocess.check_output([
                    "ffmpeg", "-y",
                    "-ss", "%d" % song['offset_seconds'],
                    '-t', str(int(split_milliseconds) / 1000.0),
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    "-i", "mp3/MC-Hammer--U-Cant-Touch-This.mp4",
                    test_file_name])
            i += 1

        subprocess.check_output("ffmpeg -y -f concat -i mylist.txt -c copy output.mp4", shell=True)

        for song in songs:
            print song

    sys.exit(0)
