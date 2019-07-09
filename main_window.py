import threading
import wx


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
        hook_manager.window_to_publish_to = self

        self.consuming = False

        wx.Panel.__init__(self, parent)
        self.textbox = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        self.horizontal = wx.BoxSizer()
        self.horizontal.Add(self.textbox, proportion=1, flag=wx.EXPAND)

        self.sizer_vertical = wx.BoxSizer(wx.VERTICAL)
        self.sizer_vertical.Add(self.horizontal, proportion=1, flag=wx.EXPAND)
        self.SetSizerAndFit(self.sizer_vertical)

    def print_to_text_box(self, event):
        print "Printing message on Thread with Id {}".format(threading.current_thread().ident)
        self.textbox.AppendText('MessageName: {}\n'.format(event.MessageName))
        self.textbox.AppendText('Message: {}\n'.format(event.Message))
        self.textbox.AppendText('Time: {}\n'.format(event.Time))
        self.textbox.AppendText('Window: {}\n'.format(event.Window))
        self.textbox.AppendText('WindowName: {}\n'.format(event.WindowName))
        self.textbox.AppendText('Position: {}\n'.format(event.Position))
        self.textbox.AppendText('Wheel: {}\n'.format(event.Wheel))
        self.textbox.AppendText('Injected: {}\n'.format(event.Injected))
        self.textbox.AppendText('---\n')
