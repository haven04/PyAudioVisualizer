import numpy
import wave
import queue
import customthreads as ct

# dic_pyaudio_dtype_to_numpy_dtype = {  1: numpy.float32,
#                                       2: numpy.int32,
#                                       8: numpy.int16,
#                                       16: numpy.int8,
#                                       32: numpy.uint8 }

dic_datawidth_to_numpy_dtype = {1: numpy.uint8,
                                2: numpy.int16,
                                4: numpy.int32}


def split_channel(data, channel):
    return numpy.transpose(numpy.reshape(data, (len(data)/channel, channel)))

def merge_channel(data):
    # data_size = len(data) * len(data[0])
    return numpy.reshape(numpy.transpose(data), data.size)

class AudioBuffer(ct.StoppableThread, ct.DispatcherThread):
    def read_with_blocksize(self, alist, blocksize=1):
        length = len(alist)
        for idx in range(0, length, blocksize):
            end_pos = idx + blocksize
            if(end_pos > length):
                end_pos = length
            yield alist[idx:end_pos]

    def __init__(self, datablock, blocksize=1024, *args, **kwargs):

        super(AudioBuffer, self).__init__(*args, **kwargs)

        self.datablock = datablock
        self.blocksize = blocksize

    def run(self):
        blockreader = self.read_with_blocksize(self.datablock, self.blocksize)
        for db in blockreader:
            if(self.is_stopped()):
                break
            self.dispatch(db)


class WavBuffer(ct.StoppableThread, ct.DispatcherThread):
    def __init__(self, filename, blocksize=1024, *args, **kwargs):
        super(WavBuffer, self).__init__(*args, **kwargs)

        self.wf = wave.open(filename, 'rb')
        self.samplerate = self.wf.getframerate()
        self.channel = self.wf.getnchannels()
        self.width = self.wf.getsampwidth()
        self.blocksize = blocksize

    def run(self):
        db = self.wf.readframes(self.blocksize)
        while db:
            if(self.is_stopped()):
                break
            self.dispatch(db)
            # self.out_queue.put(db)
            # self.out_q.task_done()
            db = self.wf.readframes(self.blocksize)


class AudioStreamer(ct.StoppableThread, ct.DispatcherThread):

    dic_numpy_dtype_to_pyaudio_dtype = {numpy.float32: 1,
                                        numpy.int32: 2,
                                        numpy.int16: 8,
                                        numpy.int8: 16,
                                        numpy.uint8: 32}

    def __init__(self, samplerate=44100, buffersize=1024, input_flag=False,
                 channel=1, datatype=numpy.int32, filename=None,
                 *args, **kwargs):

        super(AudioStreamer, self).__init__(*args, **kwargs)

        self.samplerate = samplerate
        self.datatype = datatype
        self.pyaudio_format = self.dic_numpy_dtype_to_pyaudio_dtype[self.datatype]
        self.channel = channel
        self.buffersize = buffersize
        self.in_queue = queue.Queue()
        self.input_flag = input_flag
        self.filename = filename
        if(self.filename is ''):
            self.filename = None
        self.frames = []

    def run(self):
        import pyaudio

        p = pyaudio.PyAudio()
        if(self.input_flag is True):
            stream = p.open(format=self.pyaudio_format,
                            channels=self.channel,
                            rate=self.samplerate,
                            output=False, input=True)

            while(self.is_stopped() is False):
                datablock = stream.read(self.buffersize)
                self.dispatch(numpy.frombuffer(datablock,
                                               dtype=self.datatype))
                if(self.filename is not None):
                    self.frames.append(datablock)

        else:
            stream = p.open(format=self.pyaudio_format,
                            channels=self.channel,
                            rate=self.samplerate,
                            output=True)

            while(self.is_stopped() is False):
                try:
                    datablock = self.in_queue.get_nowait()
                    stream.write(datablock)
                    self.dispatch(numpy.frombuffer(datablock,
                                                   dtype=self.datatype))
                except queue.Empty:
                    pass

        if((self.input_flag is True) and (self.filename is not None)):
            print("save")
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(self.channel)
            wf.setsampwidth(p.get_sample_size(self.pyaudio_format))
            wf.setframerate(self.samplerate)
            wf.writeframes(b''.join(self.frames))
            wf.close()

        stream.stop_stream()
        stream.close()
        p.terminate()
