import customthreads as ct
import multiprocessing
import queue
import collections
import numpy


class AudioAnalyzer(ct.StoppableProcess, ct.DispatcherProcess):
    def __init__(self, blocksize=4096, *args, **kwargs):
        super(AudioAnalyzer, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()
        self.max_value = numpy.finfo(numpy.complex128).max
        self.blocksize = blocksize
        self.deque = collections.deque(maxlen=self.blocksize)
        self.accumulated = 0

    def run(self):
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                self.deque.extend(data)
                self.accumulated += len(data)
                if(self.accumulated >= self.blocksize):
                    self.dispatch(self.fft(self.deque))
                    self.accumulated = 0

            except queue.Empty:
                '''do nothing'''
                pass

    def fft(self, datablock):
        fftblock = numpy.fft.fft(datablock)
        fftblock = numpy.fft.fftshift(fftblock)
        return fftblock
