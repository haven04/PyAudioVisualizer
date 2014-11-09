import customthreads as ct
import audiostreamer as ast
import multiprocessing
import queue
import collections
import numpy


class AudioAnalyzer(ct.StoppableProcess, ct.DispatcherProcess):
    def __init__(self, blocksize=4096, channel=1, *args, **kwargs):
        super(AudioAnalyzer, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()
        self.max_value = numpy.finfo(numpy.complex128).max
        self.channel = channel

        self.blocksize_single = blocksize
        self.blocksize_total = self.blocksize_single * self.channel
        self.accumulated_samples = 0

        self.deque_list = [collections.deque(maxlen=self.blocksize_single) for i in range(self.channel)]

    def run(self):
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = ast.split_channel(data, self.channel)
                for i in range(self.channel):
                    self.deque_list[i].extend(split_data[i])

                self.accumulated_samples += len(data)
                if(self.accumulated_samples >= self.blocksize_total):
                    analyzed_data = numpy.array([self.analyze(dq) for dq in self.deque_list])
                    self.dispatch(ast.merge_channel(analyzed_data))
                    self.accumulated_samples = 0

            except queue.Empty:
                '''do nothing'''
                pass

    def analyze(self, datablock):
        fftblock = numpy.fft.fft(datablock)
        fftblock = numpy.fft.fftshift(fftblock)
        return fftblock
