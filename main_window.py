import windows_hooks
import wx

from constants import InputTypes


class MainWindow(wx.Frame):
    def __init__(self, parent, title, hook_manager):
        wx.Frame.__init__(self, parent, title=title, size=(800, 600))
        self.hook_manager = hook_manager

        self.CreateStatusBar()

        menu_file = wx.Menu()
        menu_item_exit = menu_file.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        menu_help = wx.Menu()
        menu_item_about = menu_help.Append(wx.ID_ABOUT, "&About", " Information about this program")

        menu_bar = wx.MenuBar()
        menu_bar.Append(menu_file, "&File")
        menu_bar.Append(menu_help, "&Help")
        self.SetMenuBar(menu_bar)

        self.panel = MainPanel(self, hook_manager)

        self.Bind(wx.EVT_MENU, self.on_about, menu_item_about)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_item_exit)

        self.Show(True)

    def on_about(self, e):
        dlg = wx.MessageDialog(self, "A window to test Windows Hooks", "About Test Windows Hooks",
                               wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_exit(self, e):
        self.Close(True)


class MainPanel(wx.Panel):
    def __init__(self, parent, hook_manager):
        self.hook_manager = hook_manager
        self.consuming = False

        wx.Panel.__init__(self, parent)
        self.textbox = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.button_task = wx.Button(self, label="Long Task")
        self.button_consume = wx.Button(self, label="Start Consuming")

        self.horizontal = wx.BoxSizer()
        self.horizontal.Add(self.textbox, proportion=1, flag=wx.EXPAND)

        self.horizontal2 = wx.BoxSizer()
        self.horizontal2.Add(self.button_consume)
        self.horizontal2.Add(self.button_task)

        self.sizer_vertical = wx.BoxSizer(wx.VERTICAL)
        self.sizer_vertical.Add(self.horizontal, proportion=1, flag=wx.EXPAND)
        self.sizer_vertical.Add(self.horizontal2, proportion=1, flag=wx.CENTER)
        self.SetSizerAndFit(self.sizer_vertical)

        self.Bind(wx.EVT_BUTTON, self.on_click_task, self.button_task)
        self.Bind(wx.EVT_BUTTON, self.on_click_consume, self.button_consume)

        hook_manager.window_to_publish_to = self
        self.Connect(-1, -1, windows_hooks.WX_EVT_MOUSE_LEFT_BUTTON_DOWN_ID,
                     self.on_hooked_left_button_down)

    def on_click_task(self, event):
        self.textbox.AppendText('Starting a long task...\n')

    def on_click_consume(self, event):
        if not self.consuming:
            self.button_consume.SetLabel('Stop Consuming')
            self.hook_manager.set_user_input_types_to_consume(InputTypes.MOUSE_BUTTONS)
            self.consuming = True

        else:
            self.button_consume.SetLabel('Start Consuming')
            self.hook_manager.set_user_input_types_to_consume(InputTypes.NONE)
            self.consuming = False

    def on_hooked_left_button_down(self, event):

        # TODO - I don't know if the concept is bad or if the text box is buggy
        #        but after a few clicks the text shows unexpected text and the
        #        app eventually freezes
        self.textbox.AppendText('MessageName: {}\n'.format(event.mouse_event.MessageName))
        self.textbox.AppendText('Message: {}\n'.format(event.mouse_event.Message))
        self.textbox.AppendText('Time: {}\n'.format(event.mouse_event.Time))
        self.textbox.AppendText('Window: {}\n'.format(event.mouse_event.Window))
        self.textbox.AppendText('WindowName: {}\n'.format(event.mouse_event.WindowName))
        self.textbox.AppendText('Position: {}\n'.format(event.mouse_event.Position))
        self.textbox.AppendText('Wheel: {}\n'.format(event.mouse_event.Wheel))
        self.textbox.AppendText('Injected: {}\n'.format(event.mouse_event.Injected))
        self.textbox.AppendText('---\n')
