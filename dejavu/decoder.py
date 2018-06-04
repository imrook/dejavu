import fnmatch
import os
from hashlib import sha1

import numpy as np
from pydub.utils import audioop


def unique_hash(filepath, blocksize=2 ** 20):
    """ Small function to generate a hash to uniquely generate
    a file. Inspired by MD5 version here:
    http://stackoverflow.com/a/1131255/712997

    Works with large files. 
    """
    s = sha1()
    with open(filepath, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            s.update(buf)
    return s.hexdigest().upper()


def find_files(path, extensions):
    # Allow both with ".mp3" and without "mp3" to be used for extensions
    extensions = [e.replace(".", "") for e in extensions]

    for dirpath, dirnames, files in os.walk(path):
        for extension in extensions:
            for f in fnmatch.filter(files, "*.%s" % extension):
                p = os.path.join(dirpath, f)
                yield (p, extension)


def read(filename, audio_file):
    """
    Reads any file supported by pydub (ffmpeg) and returns the data contained
    within.

    returns: (channels, sample rate, filename hash)
    """
    channels = []
    try:
        data = np.fromstring(audio_file._data, np.int16)

        for chn in xrange(audio_file.channels):
            channels.append(data[chn::audio_file.channels])

    except audioop.error:
        pass

    return channels, audio_file.frame_rate, unique_hash(filename)


def path_to_songname(path):
    """
    Extracts song name from a filepath. Used to identify which songs
    have already been fingerprinted on disk.
    """
    return os.path.splitext(os.path.basename(path))[0]
