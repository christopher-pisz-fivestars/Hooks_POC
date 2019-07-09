from enum import Enum


class HookEvents(Enum):
    """
    An enumeration of the various input events that one can subscribe to using pubsub.
    These will be published by the WindowsHooksWrapper, found in the plugins/ui package.
    """
    mouse = 'hooks.mouse'
    mouse_left = 'hooks.mouse.left'
    mouse_left_down = 'hooks.mouse.left.down'
    mouse_left_up = 'hooks.mouse.left.up'
    mouse_right = 'hooks.mouse.right'
    mouse_right_down = 'hooks.mouse.right.down'
    mouse_right_up = 'hooks.mouse.right.up'
    mouse_move = 'hooks.mouse.move'
    keyboard = 'hooks.keyboard'
    key_down = 'hooks.keyboard.down'
    key_up = 'hooks.keyboard.up'


class InputTypes(object):
    """
    Flags to represent the different kinds of input we are acting on from the user
    """
    NONE = 0b00000000
    KEYBOARD = 0b00000001
    MOUSE_BUTTONS = 0b00000010
    MOUSE_MOVE = 0b00000100
    ALL = 0b11111111
