import pyHook
import threading
import pythoncom
import win32con
import wx
import wx.lib.newevent

from pyHook import HookConstants
from pubsub import pub
from constants import HookEvents, InputTypes

MOUSE_BUTTON_EVENTS = {HookConstants.WM_LBUTTONDOWN, HookConstants.WM_LBUTTONUP,
                       HookConstants.WM_RBUTTONDOWN, HookConstants.WM_RBUTTONUP}
HOOK_EVENT_MAP = {HookConstants.WM_LBUTTONDOWN: HookEvents.mouse_left_down.value,
                  HookConstants.WM_LBUTTONUP: HookEvents.mouse_left_up,
                  HookConstants.WM_RBUTTONDOWN: HookEvents.mouse_right_down.value,
                  HookConstants.WM_RBUTTONUP: HookEvents.mouse_right_up,
                  HookConstants.WM_MOUSEMOVE: HookEvents.mouse_move.value}

WX_EVT_MOUSE_LEFT_BUTTON_DOWN_ID = wx.NewId()


class WxHookEventMouseLeftButtonDown(wx.PyEvent):
    """
    Custom wx event for posting the left mouse button down event from the hook to the UI thread
    """
    def __init__(self):
        self.event_id = WX_EVT_MOUSE_LEFT_BUTTON_DOWN_ID
        wx.PyEvent.__init__(self)
        self.SetEventType(self.event_id)
        self.mouse_event = None


class WindowsHooksWrapper(object):
    """
    Provides a means to subscribe to keyboard and mouse events via Windows Hooks

    It is important to note that:
    * A thread specific hook (one that is not injected via dll injection) must be registered on the
      same thread with the windows msg pump or it will not work and no indication of error is given
    In discussions with the team, we made the assumptions that:
    * Falco will always register a wx app that provides the message pump
    * This class will always be instantiated on the main thread
    If those no longer hold true, this class will need to provide its own message pump on the same
    thread where hook registration takes place
    """
    def __init__(self):
        self.consuming_user_keyboard_events = False
        self.consuming_user_mouse_button_events = False
        self.consuming_user_mouse_move_events = False
        self.publishing_user_keyboard_events = True
        self.publishing_user_mouse_button_events = True
        self.publishing_user_mouse_move_events = True
        self.hook_manager = None
        self.started = False
        self.thread = threading.Thread(target=self.thread_proc)
        self.window_to_publish_to = None

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

    def set_user_input_types_to_consume(self, input_types_to_consume):
        """
        Tells the windows hooks wrapper to consume user input events or not.
        Consumed events will not be passed to other hooks or the process they were intended for.
        Injected events will always be passed on.
        :param input_types_to_consume: Flag. Some bitwise combination of the InputTypes enum that
            represents each type of input and whether to consume user events of that type or not
        """

        # if input_types_to_consume & InputTypes.KEYBOARD:
        #     if not self.consuming_user_keyboard_events:
        #         logger.debug('Consuming user keyboard events')
        # else:
        #     if self.consuming_user_keyboard_events:
        #         logger.debug('No longer consuming user keyboard events')
        #
        # if input_types_to_consume & InputTypes.MOUSE_BUTTONS:
        #     if not self.consuming_user_mouse_button_events:
        #         logger.debug('Consuming user mouse button events')
        # else:
        #     if self.consuming_user_mouse_button_events:
        #         logger.debug('No longer consuming user mouse button events')
        #
        # if input_types_to_consume & InputTypes.MOUSE_MOVE:
        #     if not self.consuming_user_mouse_move_events:
        #         logger.debug('Consuming user mouse move events')
        # else:
        #     if self.consuming_user_mouse_move_events:
        #         logger.debug('No longer consuming user mouse move events')

        self.consuming_user_keyboard_events = (input_types_to_consume & InputTypes.KEYBOARD)
        self.consuming_user_mouse_button_events = \
            (input_types_to_consume & InputTypes.MOUSE_BUTTONS)
        self.consuming_user_mouse_move_events = (input_types_to_consume & InputTypes.MOUSE_MOVE)

    def set_user_input_types_to_publish(self, input_types_to_publish):
        """
        Tells the windows hooks wrapper to publish user input events or not.
        :param input_types_to_publish: Flag. Some bitwise combination of the InputTypes enum
            that represents each type of input and whether to publish user events of that type
        """

        # if input_types_to_publish & InputTypes.KEYBOARD:
        #     if not self.publishing_user_keyboard_events:
        #         logger.debug('Publishing user keyboard events')
        # else:
        #     if self.publishing_user_keyboard_events:
        #         logger.debug('No longer Publishing user keyboard events')
        #
        # if input_types_to_publish & InputTypes.MOUSE_BUTTONS:
        #     if not self.publishing_user_mouse_button_events:
        #         logger.debug('Publishing user mouse button events')
        # else:
        #     if self.publishing_user_mouse_button_events:
        #         logger.debug('No longer Publishing user mouse button events')
        #
        # if input_types_to_publish & InputTypes.MOUSE_MOVE:
        #     if not self.publishing_user_mouse_move_events:
        #         logger.debug('Publishing user mouse move events')
        # else:
        #     if self.publishing_user_mouse_move_events:
        #         logger.debug('No longer Publishing user mouse move events')

        self.publishing_user_keyboard_events = (input_types_to_publish & InputTypes.KEYBOARD)
        self.publishing_user_mouse_button_events = (
            input_types_to_publish & InputTypes.MOUSE_BUTTONS)
        self.publishing_user_mouse_move_events = (input_types_to_publish & InputTypes.MOUSE_MOVE)

    def on_keyboard_event(self, event):
        """
        Called back from pyHooks library on a keyboard event
        :param event: event passed from pyHooks
        :return: True if we are to pass the event on to other hooks and the process it was intended
         for. False to consume the event.
        """
        # When the user presses the escape key, we shall stop consuming events, so they may regain
        # control in if they got stuck in a bad state where input was being consumed when they did
        # not expect it?
        if event.KeyID == win32con.VK_ESCAPE and not event.Injected:
            consume = self.consuming_user_keyboard_events
            publish = self.publishing_user_keyboard_events
            #logger.debug('Escape key hit. Turning input blocking off.')
            self.set_user_input_types_to_consume(InputTypes.NONE)
        else:
            # Event was not user failsafe key event
            if event.Injected:
                # Always publish injected events
                # Do not consume injected events
                publish = True
                consume = False
            else:
                publish = self.publishing_user_keyboard_events
                consume = self.consuming_user_keyboard_events

        if publish:
            if event.Message == HookConstants.WM_KEYDOWN:
                pub.sendMessage(HookEvents.key_down.value, event=event)
            elif event.Message == HookConstants.WM_KEYUP:
                pub.sendMessage(HookEvents.key_up.value, event=event)

        return not consume

    def on_mouse_event(self, event):
        """
        Called back from pyHooks library on a mouse event
        :param event: event passed from pyHooks
        :return: True if we are to pass the event on to other hooks and the process it was intended
         for. False to consume the event.
        """
        publish = True
        consume = False

        #logger.dev("Received a mouse event with Message: {} Injected: {}", event.Message, event.Injected)

        if event.Injected:
            # Always publish injected events
            # Do not consume injected events
            publish = True
            consume = False

        elif event.Message in MOUSE_BUTTON_EVENTS:
            publish = self.publishing_user_mouse_button_events
            consume = self.consuming_user_mouse_button_events

        elif event.Message == HookConstants.WM_MOUSEMOVE:
            publish = self.publishing_user_mouse_move_events
            consume = self.consuming_user_mouse_move_events

        if publish:
            if self.window_to_publish_to:
                if event.Message == HookConstants.WM_LBUTTONDOWN:
                    wx_hook_event = WxHookEventMouseLeftButtonDown()
                    wx_hook_event.mouse_event = event
                    wx.PostEvent(self.window_to_publish_to, wx_hook_event)

            # #logger.dev("Publishing mouse event {}", event.Message)
            # if event.Message == HookConstants.WM_LBUTTONDOWN:
            #     pub.sendMessage(HookEvents.mouse_left_down.value, event=event)
            # elif event.Message == HookConstants.WM_LBUTTONUP:
            #     pub.sendMessage(HookEvents.mouse_left_up.value, event=event)
            # elif event.Message == HookConstants.WM_RBUTTONDOWN:
            #     pub.sendMessage(HookEvents.mouse_right_down.value, event=event)
            # elif event.Message == HookConstants.WM_RBUTTONUP:
            #     pub.sendMessage(HookEvents.mouse_right_up.value, event=event)
            # elif event.Message == HookConstants.WM_MOUSEMOVE:
            #     pub.sendMessage(HookEvents.mouse_move.value, event=event)

        #if consume:
            #logger.dev("Consumed mouse event {}", event.Message)

        return not consume

    def thread_proc(self):
        print "Thread started"

        # Evidently, the hook must be registered on the same thread with the windows msg pump or
        #     it will not work and no indication of error is seen
        # Also note that for exception safety, when the hook manager goes out of scope, the
        #     documentation says that it unregisters all outstanding hooks
        self.hook_manager = pyHook.HookManager()
        self.hook_manager.KeyAll = self.on_keyboard_event
        self.hook_manager.HookKeyboard()
        self.hook_manager.MouseAll = self.on_mouse_event
        self.hook_manager.HookMouse()

        while self.started:
            pythoncom.PumpWaitingMessages()

        print "Thread exiting..."

        self.hook_manager.UnhookKeyboard()
        self.hook_manager.UnhookMouse()
        self.hook_manager = None
