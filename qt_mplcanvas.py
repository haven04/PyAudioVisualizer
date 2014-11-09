from PyQt5 import QtWidgets

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import audiostreamer as ast
import threading
from threading import Lock
import multiprocessing
import customthreads
import queue
import collections


class MplCanvas(FigureCanvasQTAgg, customthreads.StoppableThread):

    def __init__(self, xlim=None, ylim=None, channel=1, x_range=None,
                 parent=None, post_process=None, width=5, height=4, dpi=100,
                 *args, **kwargs):

        customthreads.StoppableThread.__init__(self, *args, **kwargs)

        self.lock = Lock()
        self.in_queue = queue.Queue()

        self.xlim = xlim
        self.ylim = ylim
        self.x_range = x_range

        if(self.x_range is None):
            self.x_range = range(self.xlim[0], self.xlim[1])

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvasQTAgg.__init__(self, self.fig)
        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.axes_list = []
        self.setParent(parent)

        self.set_channel(channel)

        self.post_process = post_process
        if(self.post_process is None):
            self.post_process = lambda data: data

    def set_channel(self, channel):
        self.lock.acquire()

        self.channel = channel

        '''clear subplots'''
        if(self.axes_list is not []):
            for ax in self.axes_list:
                self.fig.delaxes(ax)

        self.axes_list = []
        for i in range(1, self.channel+1):
            self.axes_list.append(self.fig.add_subplot(self.channel, 1, i))
            self.axes_list[i-1].hold(False)

        self.lock.release()

    def run(self):
        print(self.x_range)
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = ast.split_channel(data, self.channel)
                p_split_data = [self.post_process(sd) for sd in split_data]

                self.lock.acquire()
                for i in range(self.channel):
                    self.axes_list[i].plot(self.x_range, p_split_data[i], 'b')
                    self.axes_list[i].set_xlim(self.xlim)
                    self.axes_list[i].set_ylim(self.ylim)
                self.draw()
                self.lock.release()

            except queue.Empty:
                pass


class DequeMplCanvas(MplCanvas):

    def __init__(self, max_size=44100, redraw_interval=None,
                 *args, **kwargs):
        self.max_deque_size = max_size
        self.deque_list = []
        self.redraw_interval = redraw_interval
        super(DequeMplCanvas, self).__init__(*args, **kwargs)

    def set_channel(self, channel):
        super(DequeMplCanvas, self).set_channel(channel)
        self.lock.acquire()
        self.deque_list = [collections.deque(maxlen=self.max_deque_size) for i in range(self.channel)]
        for dq in self.deque_list:
            dq.extend([0] * self.max_deque_size)
        self.lock.release()

    def redraw(self):
        self.lock.acquire()
        for i in range(self.channel):
            self.axes_list[i].plot(self.x_range, self.deque_list[i], 'b')
            self.axes_list[i].set_xlim(self.xlim)
            self.axes_list[i].set_ylim(self.ylim)
        self.draw()
        self.lock.release()

    def redraw_with_timer(self):
        '''redraw graph every 'redraw_interval' seconds'''
        self.redraw()
        self.lock.acquire()
        if(self.is_running()):
            threading.Timer(self.redraw_interval, self.redraw_with_timer).start()
        self.lock.release()

    def run(self):
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


class MplCanvasWithMPQueue(MplCanvas):
    def __init__(self, *args, **kwargs):
        super(MplCanvasWithMPQueue, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()

class DequeMplCanvasWithMpQueue(DequeMplCanvas):
    def __init__(self, *args, **kwargs):
        super(DequeMplCanvasWithMpQueue, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()
