from pydub import AudioSegment

import dejavu.fingerprint as fingerprint
import dejavu.decoder as decoder
import numpy as np
import pyaudio
import time


class BaseRecognizer(object):

    def __init__(self, dejavu):
        self.dejavu = dejavu
        self.Fs = fingerprint.DEFAULT_FS

    def _recognize(self, *data):
        matches = []
        for d in data:
            matches.extend(self.dejavu.find_matches(d, Fs=self.Fs))
        return self.dejavu.align_matches(matches)

    def recognize(self):
        pass  # base class does nothing


class FileRecognizer(BaseRecognizer):
    def __init__(self, dejavu):
        super(FileRecognizer, self).__init__(dejavu)

    def recognize_file(self, filename, split_milliseconds, start_milliseconds, limit_milliseconds):

        matches = []
        audiofile = AudioSegment.from_file(filename)
        max_milliseconds = audiofile.duration_seconds * 1000 - start_milliseconds

        if limit_milliseconds is not None and max_milliseconds > limit_milliseconds:
            max_milliseconds = limit_milliseconds

        segments = np.math.ceil(max_milliseconds / split_milliseconds)
        for seg in range(0, int(segments)):
            start = start_milliseconds + seg * split_milliseconds
            frames, self.Fs, file_hash = decoder.read(filename, audiofile, split_milliseconds, start)

            t = time.time()
            match = self._recognize(*frames)
            t = time.time() - t

            if match:
                match['match_time'] = t

            matches.append(match)

        return matches

    def recognize(self, filename=None, split_milliseconds=10000, start_milliseconds=0, limit_milliseconds=None):
        return self.recognize_file(filename, split_milliseconds, start_milliseconds, limit_milliseconds)


class MicrophoneRecognizer(BaseRecognizer):
    default_chunksize = 8192
    default_format = pyaudio.paInt16
    default_channels = 2
    default_samplerate = 44100

    def __init__(self, dejavu):
        super(MicrophoneRecognizer, self).__init__(dejavu)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.data = []
        self.channels = MicrophoneRecognizer.default_channels
        self.chunksize = MicrophoneRecognizer.default_chunksize
        self.samplerate = MicrophoneRecognizer.default_samplerate
        self.recorded = False

    def start_recording(self, channels=default_channels,
                        samplerate=default_samplerate,
                        chunksize=default_chunksize):
        self.chunksize = chunksize
        self.channels = channels
        self.recorded = False
        self.samplerate = samplerate

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.stream = self.audio.open(
            format=self.default_format,
            channels=channels,
            rate=samplerate,
            input=True,
            frames_per_buffer=chunksize,
        )

        self.data = [[] for i in range(channels)]

    def process_recording(self):
        data = self.stream.read(self.chunksize)
        nums = np.fromstring(data, np.int16)
        for c in range(self.channels):
            self.data[c].extend(nums[c::self.channels])

    def stop_recording(self):
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.recorded = True

    def recognize_recording(self):
        if not self.recorded:
            raise NoRecordingError("Recording was not complete/begun")
        return self._recognize(*self.data)

    def get_recorded_time(self):
        return len(self.data[0]) / self.rate

    def recognize(self, limit_milliseconds=10000):
        self.start_recording()
        segments = int(self.samplerate / self.chunksize * limit_milliseconds / 1000.0)
        for i in range(0, segments):
            self.process_recording()
        self.stop_recording()
        return [self.recognize_recording()]


class NoRecordingError(Exception):
    pass
