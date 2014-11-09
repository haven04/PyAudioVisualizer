import multiprocessing
import threading


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()

    def is_stopped(self):
        return self._stop_flag.is_set()

    def is_running(self):
        return not(self._stop_flag.is_set())

    def immediate_join(self):
        self.stop()
        self.join()


class DispatcherThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(DispatcherThread, self).__init__(*args, **kwargs)
        self._queuelist = []

    def register_queue(self, q):
        self._queuelist.append(q)

    def dispatch(self, data):
        for q in self._queuelist:
            q.put(data)


class StoppableProcess(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        super(StoppableProcess, self).__init__(*args, **kwargs)
        self._stop_flag = multiprocessing.Event()

    def stop(self):
        self._stop_flag.set()

    def is_stopped(self):
        return self._stop_flag.is_set()

    def is_running(self):
        return not(self._stop_flag.is_set())

    def immediate_join(self):
        self.stop()
        self.join()


class DispatcherProcess(multiprocessing.Process):

    def __init__(self, *args, **kwargs):
        super(DispatcherProcess, self).__init__(*args, **kwargs)
        self._queuelist = []

    def register_queue(self, q):
        self._queuelist.append(q)

    def dispatch(self, data):
        for q in self._queuelist:
            q.put(data)
