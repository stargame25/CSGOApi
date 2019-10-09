import threading
import traceback
from ctypes import pythonapi, py_object
from flask_login import UserMixin


class User(UserMixin):
    id = None
    username = None
    api = None
    settings = None

    def __init__(self, _username, _api, _settings):
        self.username = _username
        self.api = _api
        self.settings = _settings

    def get_id(self):
        return self.username


class AsyncTask(threading.Thread):
    def __init__(self, username="", name="", method=None):
        threading.Thread.__init__(self)
        self.username = username
        self.name = name
        self.method = method
        self.finished = False if method else True

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        res = pythonapi.PyThreadState_SetAsyncExc(thread_id, py_object(SystemExit))
        if res > 1:
            pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        else:
            self.finished = True

    def run(self):
        try:
            if self.method:
                self.method()
        except Exception as e:
            print("Error occurred in user-thread. User: " + str(self.username))
            #logg(str(traceback.format_exc()))
        self.finished = True
