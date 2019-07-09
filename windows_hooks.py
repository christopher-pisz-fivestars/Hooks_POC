import pyHook
import threading
import pythoncom


class WindowsHooksWrapper(object):
    def __init__(self):
        self.hook_manager = None
        self.started = False
        self.thread = threading.Thread(target=self.thread_proc)
        self.window_to_publish_to = None

        print "HookWrapper created on Id {}".format(threading.current_thread().ident)

    def __del__(self):
        self.stop()

    def start(self):
        if self.started:
            self.stop()

        self.started = True
        self.thread.start()

    def stop(self):
        if not self.started:
            return

        self.started = False
        self.thread.join()

    def on_mouse_event(self, event):
        """
        Called back from pyHooks library on a mouse event
        :param event: event passed from pyHooks
        :return: True if we are to pass the event on to other hooks and the process it was intended
         for. False to consume the event.
        """

        if self.window_to_publish_to:
            from twisted.internet import reactor
            reactor.callFromThread(self.window_to_publish_to.print_to_text_box, event)
        return True

    def thread_proc(self):
        print "Thread started with Id {}".format(threading.current_thread().ident)

        # Evidently, the hook must be registered on the same thread with the windows msg pump or
        #     it will not work and no indication of error is seen
        # Also note that for exception safety, when the hook manager goes out of scope, the
        #     documentation says that it unregisters all outstanding hooks
        self.hook_manager = pyHook.HookManager()
        self.hook_manager.MouseAll = self.on_mouse_event
        self.hook_manager.HookMouse()

        while self.started:
            pythoncom.PumpMessages()

        print "Thread exiting..."

        self.hook_manager.UnhookMouse()
        self.hook_manager = None
