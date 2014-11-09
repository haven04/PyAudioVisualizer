import multiprocessing
from multiprocessing import Lock
import audiostreamer as ast
import threading
import queue
import customthreads as ct
import collections


class MPlot(ct.StoppableProcess):
    def __init__(self, xlim, ylim, channel=1, post_process=None, x_range=None,
                 *args, **kwargs):
        super(MPlot, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()
        self.xlim = xlim
        self.ylim = ylim
        self.x_range = x_range
        if(self.x_range is None):
            self.x_range = range(self.xlim[0], self.xlim[1])

        self.lock = Lock()
        self.channel = channel

        self.post_process = post_process
        if(self.post_process is None):
            self.post_process = lambda data: data

    def init_plot(self):
        self.lock.acquire()
        import matplotlib.pyplot as plt

        self.fig, self.axarr = plt.subplots(self.channel,
                                            sharex=True,
                                            squeeze=False)
        for i in range(self.channel):
            self.axarr[i, 0].hold(False)
        self.fig.show()

        self.lock.release()

    def run(self):
        self.init_plot()
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = ast.split_channel(data, self.channel)
                p_split_data = [self.post_process(sd) for sd in split_data]

                self.lock.acquire()
                for i in range(self.channel):
                    self.axarr[i, 0].plot(self.x_range, p_split_data[i])
                    self.axarr[i, 0].set_xlim(self.xlim)
                    self.axarr[i, 0].set_ylim(self.ylim)
                self.fig.canvas.draw()
                self.lock.release()

            except queue.Empty:
                pass


class DequeMPlot(MPlot):
    def __init__(self, max_size=44100, redraw_interval=None,
                 *args, **kwargs):
        super(DequeMPlot, self).__init__(*args, **kwargs)
        self.max_deque_size = max_size
        self.deque_list = [collections.deque(maxlen=self.max_deque_size) for i in range(self.channel)]

        for dq in self.deque_list:
            dq.extend([0] * max_size)

        self.redraw_interval = redraw_interval

    def redraw(self):
        self.lock.acquire()
        for i in range(self.channel):
            self.axarr[i, 0].plot(self.x_range, self.deque_list[i])
            self.axarr[i, 0].set_xlim(self.xlim)
            self.axarr[i, 0].set_ylim(self.ylim)
        self.fig.canvas.draw()
        self.lock.release()

    def redraw_with_timer(self):
        self.redraw()
        self.lock.acquire()
        threading.Timer(self.redraw_interval, self.redraw_with_timer).start()
        self.lock.release()

    def run(self):
        self.init_plot()

        if(self.redraw_interval is not None):
            self.redraw_with_timer()

        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = ast.split_channel(data, self.channel)
                p_split_data = [self.post_process(sd) for sd in split_data]

                for i in range(self.channel):
                    self.deque_list[i].extend(p_split_data[i])
                if(self.redraw_interval is None):
                    self.redraw()
            except queue.Empty:
                pass
