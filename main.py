import time
import pyautogui
import wx

from windows_hooks import WindowsHooksWrapper
from main_window import MainWindow


def main():
    hook_wrapper = WindowsHooksWrapper()
    hook_wrapper.start()

    app = wx.App(False)
    frame = MainWindow(None, 'Hooks Testing', hook_wrapper)
    app.MainLoop()

    hook_wrapper.stop()


if __name__ == "__main__":
    main()
