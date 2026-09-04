"""Проверка настоящего системного Ctrl+V: SendInput в собственное окно."""
import ctypes
import sys
import time

sys.path.insert(0, r"d:\Загрузки\VideoGrab")
import app

user32 = ctypes.windll.user32

VK_CONTROL, VK_V = 0x11, 0x56
KEYEVENTF_KEYUP = 0x0002

root = app.App()
root.update()
root.clipboard_clear()
root.clipboard_append("https://example.com/real-input")
root.update()

target = int(root.frame(), 16)
fg = user32.GetForegroundWindow()
fg_tid = user32.GetWindowThreadProcessId(fg, None)
my_tid = ctypes.windll.kernel32.GetCurrentThreadId()
user32.AttachThreadInput(my_tid, fg_tid, True)
ok_fg = user32.SetForegroundWindow(target)
user32.BringWindowToTop(target)
time.sleep(0.4)
root.update()
print("SetForegroundWindow:", ok_fg, "fg now is target:", user32.GetForegroundWindow() == target)

user32.keybd_event(VK_CONTROL, 0, 0, 0)
user32.keybd_event(VK_V, 0, 0, 0)
user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

deadline = time.time() + 3
while time.time() < deadline:
    root.update()
    time.sleep(0.05)

got = root.url_entry.get()
print("REAL_CTRL_V:", repr(got))
root.destroy()
sys.exit(0 if got == "https://example.com/real-input" else 1)
