import time

import numpy as np
from pydub import AudioSegment

import dejavu.decoder as decoder
import dejavu.fingerprint as fingerprint


class FileRecognizer:

    def __init__(self, dejavu):
        self.dejavu = dejavu
        self.Fs = fingerprint.DEFAULT_FS

    def _recognize(self, *data):
        matches = []
        for d in data:
            matches.extend(self.dejavu.find_matches(d, Fs=self.Fs))
        return self.dejavu.align_matches(matches)

    def recognize_file(self, filename, split_milliseconds, start_milliseconds, limit_milliseconds):

        matches = []
        audio_file = AudioSegment.from_file(filename)
        max_milliseconds = audio_file.duration_seconds * 1000 - start_milliseconds

        if limit_milliseconds is not None and max_milliseconds > limit_milliseconds:
            max_milliseconds = limit_milliseconds

        segments = np.math.ceil(max_milliseconds / split_milliseconds)
        for seg in range(0, int(segments)):
            start = start_milliseconds + seg * split_milliseconds
            temp_audio_file = audio_file[start:start + split_milliseconds]
            frames, self.Fs, file_hash = decoder.read(filename, temp_audio_file)

            t = time.time()
            match = self._recognize(*frames)
            t = time.time() - t

            if match:
                match['match_time'] = t

            matches.append(match)

        return matches

    def recognize(self, filename=None, split_milliseconds=10000, start_milliseconds=0, limit_milliseconds=None):
        return self.recognize_file(filename, split_milliseconds, start_milliseconds, limit_milliseconds)


class NoRecordingError(Exception):
    pass
