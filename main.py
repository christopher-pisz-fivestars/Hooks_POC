import wx
from twisted.internet import wxreactor

from windows_hooks import WindowsHooksWrapper
from main_window import MainWindow


def main():
    hook_wrapper = WindowsHooksWrapper()
    hook_wrapper.start()

    app = wx.App(False)
    frame = MainWindow(None, 'Hooks Testing', hook_wrapper)

    from twisted.internet import reactor
    reactor.registerWxApp(app)
    reactor.run()

    hook_wrapper.stop()


if __name__ == "__main__":
    wxreactor.install()
    main()
