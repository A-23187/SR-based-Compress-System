#!/usr/bin/env python3
import wx
import os
import srp


class DropListener(wx.FileDropTarget):
    def __init__(self):
        wx.FileDropTarget.__init__(self)

    def OnDropFiles(self, x, y, infiles):
        infile = infiles[0]
        fname, fext = os.path.splitext(infile)
        try:
            if fext == '.srp':
                srp.show(infile)
            else:
                msg = 'Save file as: '
                dlg = wx.TextEntryDialog(
                    None, msg, 'Save', fname + '.srp', wx.OK | wx.CANCEL)
                if dlg.ShowModal() == wx.ID_OK:
                    outfile = dlg.GetValue()
                    srp.compress(infile, outfile)
                else:
                    pass
                dlg.Destroy()
        except OSError as err:
            errdlg = wx.MessageDialog(None, f'{err}', 'Error', wx.OK)
            errdlg.ShowModal()
            errdlg.Destroy()

        # code for error tip
        # errdlg = wx.MessageDialog(None, 'content', 'title', wx.OK)
        # errdlg.ShowModal() # show it
        # errdlg.Destroy() # destroy it
        return True


class MainFrame(wx.Frame):

    def __init__(self, title):
        wx.Frame.__init__(self, None, wx.ID_ANY, title, size=(400, 220))
        self.label = wx.StaticText(self, style=wx.ALIGN_CENTER)

    def setLabelText(self, text):
        # TODO a smarter way to align center in vetical rather than use \n\n\n
        self.label.SetLabel('\n\n\n' + text)
        # self.label.SetBackgroundColour('red')

    def registerDropPicListener(self, listener):
        self.SetDropTarget(listener)


class MainApp(wx.App):

    def __init__(self, title):
        wx.App.__init__(self)
        self.frame = MainFrame(title)

    def setIcon(self, icon):
        self.frame.SetIcon(icon)


def main():
    app = MainApp('SR-based Compress System')
    app.setIcon(wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO))

    frm = app.frame
    frm.setLabelText('Please drag a picture in here to compress or show it.')
    frm.registerDropPicListener(DropListener())
    frm.Show()

    app.MainLoop()


if __name__ == '__main__':
    main()
