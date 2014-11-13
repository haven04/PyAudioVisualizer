import customthreads as ct
import audiostreamer as ast
import multiprocessing
import queue
import collections
import numpy as np


class AudioAnalyzer(ct.StoppableProcess, ct.DispatcherProcess):
    def __init__(self, blocksize=4096, overlap=1024, channel=1, *args, **kwargs):
        super(AudioAnalyzer, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()
        self.max_value = np.finfo(np.complex128).max
        self.channel = channel

        self.blocksize_single = blocksize
        self.overlapsize = overlap
        self.blocksize_total = self.blocksize_single * self.channel
        self.accumulated_samples = 0
        queue_length = self.blocksize_single + self.overlapsize
        self.deque_list = [collections.deque(maxlen=queue_length) for i in range(self.channel)]
        for dq in self.deque_list:
            dq.extend([0] * queue_length)
        self.extended_block = [0 for i in range((self.blocksize_single * 2))]
        self.window = np.hanning(self.blocksize_single)

    def run(self):
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = ast.split_channel(data, self.channel)
                for i in range(self.channel):
                    self.deque_list[i].extend(split_data[i])

                self.accumulated_samples += len(data)
                if(self.accumulated_samples >= self.blocksize_total):
                    analyzed_data = np.array([self.analyze(dq) for dq in self.deque_list])
                    self.dispatch(ast.merge_channel(analyzed_data))
                    self.accumulated_samples = 0

            except queue.Empty:
                '''do nothing'''
                pass

    def analyze(self, datablock):
        datablock = list(datablock)
        datablock = datablock[int(self.overlapsize/2) : self.blocksize_single + int(self.overlapsize/2)]
        datablock = datablock * self.window
        self.extended_block[0:self.blocksize_single] = datablock
        fftblock = np.fft.rfft(self.extended_block)

        return fftblock[0:self.blocksize_single]
