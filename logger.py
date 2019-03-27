import json
import logging
import queue
import threading

# FixMe Add docstrings!

class LogWorker(threading.Thread):

    def __init__(self, msg_queue, log_path):
        super().__init__()
        self.logger = self._set_up_logger(log_path)
        self.path = log_path
        self._msg_queue = msg_queue
        self._stop_request = threading.Event()


    def _set_up_logger(self, path):

        # Using the std lib logging module as I can assume that it
        # does reasonable things around ensuring that buffered writes
        # are flushed to the file in a timely manner. Also, this would
        # allow one and the same file to contain the log of msgs from
        # the client over the socket and any warnings, etc, logged
        # from the server app itself. (Presently, the server isn't
        # using this facility: FixMe Also, not immediately obvious how
        # that would work, given that I am using a msg queue as the
        # log msg source. ThinkMe)
        logger = logging.getLogger('socket_demo_application')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(path)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
        return logger


    def run(self):
        while not self._stop_request.isSet():
            try:
                # Make reading blocking, but timeout fairly soon so
                # that any stop request can be processed promptly.
                msg = self._msg_queue.get(True, 0.01)
            except queue.Empty:
                # Expected if self._msg_queue.get timed out. Just carry on
                continue
            self.log(msg)
            self._msg_queue.task_done()


    def join(self):
        self._stop_request.set()
        super().join()


    def log(self, msg):
        timestamp, source, msg = msg
        # Structured logging FTW
        log_msg = json.dumps(
            {'timestamp':timestamp.isoformat(),
             'source':source,
             'msg':str(msg)})
        self.logger.info(log_msg)
