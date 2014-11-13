import audioanalyzer as aa
import audiostreamer as ast


class AudioManager:
    def __init__(self, analyzer_blocksize):
        self.audiobuffer = None
        self.streamer = None
        self.analyzer = None
        self.analyzer_blocksize = analyzer_blocksize

    def set_play_wav_file(self, filename):

        self.audiobuffer = ast.WavBuffer(filename, daemon=True)

        self.samplerate = self.audiobuffer.samplerate
        self.channel = self.audiobuffer.channel
        self.dtype = ast.dic_datawidth_to_numpy_dtype[self.audiobuffer.width]

        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=False,
                                          daemon=True)

        self.analyzer = aa.AudioAnalyzer(blocksize=self.analyzer_blocksize,
                                         overlap=1024,
                                         channel=self.channel,
                                         daemon=True)

        self.audiobuffer.register_queue(self.streamer.in_queue)
        self.streamer.register_queue(self.analyzer.in_queue)

    def set_play_audiodata(self, datablock, samplerate, channel, dtype):

        self.dtype = dtype
        self.samplerate = samplerate
        self.channel = channel
        self.audiobuffer = ast.AudioBuffer(datablock, daemon=True)
        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=False,
                                          daemon=True)

        self.analyzer = aa.AudioAnalyzer(blocksize=self.analyzer_blocksize,
                                         channel=self.channel,
                                         daemon=True)

        self.audiobuffer.register_queue(self.streamer.in_queue)
        self.streamer.register_queue(self.analyzer.in_queue)

    def set_record(self, samplerate, channel, dtype, filename):

        self.dtype = dtype
        self.audiobuffer = None
        self.samplerate = samplerate
        self.channel = channel
        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=True,
                                          filename=filename,
                                          daemon=True)

        self.analyzer = aa.AudioAnalyzer(blocksize=self.analyzer_blocksize,
                                         channel=self.channel,
                                         daemon=True)
        self.streamer.register_queue(self.analyzer.in_queue)

    def start(self):
        if(self.streamer is not None):
            self.streamer.start()
        if(self.audiobuffer is not None):
            self.audiobuffer.start()
        if(self.analyzer is not None):
            self.analyzer.start()

    def stop(self):
        if((self.audiobuffer is not None) and (self.audiobuffer.is_running)):
            self.audiobuffer.immediate_join()
        if((self.streamer is not None) and (self.streamer.is_running)):
            self.streamer.immediate_join()
        if((self.analyzer is not None) and (self.analyzer.is_running)):
            self.analyzer.immediate_join()

    def is_running(self):
        result_flag = False
        if(self.audiobuffer is not None):
            result_flag = self.audiobuffer.is_running()
        if(self.streamer is not None):
            result_flag = result_flag or self.streamer.is_running()
        if(self.analyzer is not None):
            result_flag = result_flag or self.analyzer.is_running()

        return result_flag
