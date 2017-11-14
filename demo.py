from __future__ import division, print_function, unicode_literals
import pynput.mouse as Mouse
import pynput.keyboard as Keyboard
import time
import gtk
import requests
import json
from Tkinter import *
import re
from threading import Thread
gtk.gdk.threads_init()
"""
event.value = 1: key down
event.value = 0: key up
event.value = 2: key hold
"""
# device = evdev.InputDevice('/dev/input/event6')
# for event in device.read_loop():
#     if event.value == 589825:
#         print(evdev.util.categorize(event))

ctrl_btn_press = False
mouse_release = False
def timed_join_all(threads, timeout):
    start = cur_time = time.time()
    while cur_time <= (start + timeout):
        for thread in threads:
            if not thread.is_alive():
                thread.join()
        time.sleep(1)
        cur_time = time.time()

def on_move(x, y):
    print('Pointer moved to {0}'.format( (x, y)))

curr = time.time()
def on_click(x, y, button, pressed):
    global mouse_release
    global curr
    print('{0} at {1}'.format( 'Pressed' if pressed else 'Released', (x, y)))
    if pressed:
        mouse_release = False
        print("Mouse Press")
        if time.time() - curr < 0.25:
            print("Double click {}".format((x,y)))
        else:
            curr = time.time()
    else:
        mouse_release = True
        print("Mouse Release")
    
def on_scroll(x, y, dx, dy):
    print('Scrolled {0}'.format((x, y)))
    print('Scroll vector {0}'.format((dx, dy)))


isCatchWords = False
catchedWords = None
def on_press(key):
    global ctrl_btn_press
    global isCatchWords
    global catchedWords
    try:
        # print('alphanumeric key {0} pressed'.format(key.char))
        if isCatchWords:
            catchedWords += key.char
        if key.char == 'i' and ctrl_btn_press:
            isCatchWords = True
            catchedWords = ""
    except AttributeError:
        if key == Keyboard.Key.ctrl:
            ctrl_btn_press = True
        if key == Keyboard.Key.space:
            catchedWords += " "
        if key == Keyboard.Key.backspace:
            catchedWords = catchedWords[:-1]
        if key == Keyboard.Key.enter:
            isCatchWords = False
            print("\nCatched words: ", catchedWords)
            lookup(catchedWords)
            catchedWords = ""
        # print('special key {0} pressed'.format(key))

def on_release(key):
    global ctrl_btn_press
    # print('{0} released'.format(key))
    if key == Keyboard.Key.ctrl:
        ctrl_btn_press = False
    if key == Keyboard.Key.esc:
        # Stop listener
        return False

def close_when_lost_focus(event):
    print("action: close widget")
    parentName = event.widget.winfo_parent()
    parent = event.widget._nametowidget(parentName)
    parent.destroy()
    return

def make_text_popup(content, lookupText):
    root = Tk()
    root.title("Simple Dictionary")
    txt = Text(root, width=60, height=20, wrap="word")
    cnt = 0
    for sen in content['sentences']:
        cnt += 1
        en_sen = sen['fields']['en']
        vi_sen = sen['fields']['vi']
	if vi_sen[-1] == '\n':
	    display_sentence = str(cnt) + ". " + en_sen + ": " + vi_sen
	else:
	    display_sentence = str(cnt) + ". " + en_sen + ": " + vi_sen + "\n"
        txt.insert(INSERT, display_sentence)
        pattern = re.compile('(\w+\-)*(' + lookupText + ')(\-\w+)*', re.IGNORECASE)
        indexes = [(m.start(0), m.end(0), m.group(0)) for m in re.finditer(pattern, display_sentence)]
        for (start, end, group) in indexes:
	    # print("{}. {} - {}".format(cnt, start, end))
            txt.tag_add("look_up_text", str(cnt) + "." + str(start), str(cnt) + "." + str(end))
    
    txt.tag_config("look_up_text", font='helvetica 11 bold', relief='raised')
    txt.insert(END, "---------------------------END---------------------------")
    txt.config(state=DISABLED)
    txt.bind("<Leave>", close_when_lost_focus)
    txt.pack()
    root.mainloop()

def _clipboard_changed(clipboard, event):
    global ctrl_btn_press
    # global mouse_release
    # print("clipboard changed")
    if not ctrl_btn_press: 
       return
    else:
       ctrl_btn_press = False

    text = clipboard.wait_for_text()
    lookup(text)

def lookup(text):
    print("Looking up for: ", text)
    url = 'http://api.tracau.vn/WBBcwnwQpV89/'+text+'/en/JSON_CALLBACK'
    response = requests.get(url)
    if response.ok:
        response.encoding = "utf-8"
        content = response.text
        content = content[14:-3]
        content = re.compile(r'<.*?>').sub("", content)
        content = json.loads(content)
        if len(content['sentences']) == 0:
            print("no information")
            return                                                                      # display popup to show result
        make_text_popup(content, text)

if __name__=="__main__":

    mouseListener =  Mouse.Listener( on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    keyboardListener =  Keyboard.Listener( on_press=on_press, on_release=on_release)
    # mouseListener.start()
    keyboardListener.start()
    print("Simple Dictionary is running...")
    clip = gtk.clipboard_get(gtk.gdk.SELECTION_PRIMARY)
    clip.connect("owner-change", _clipboard_changed)
    gtk.main()

    
