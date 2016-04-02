"""
PC-BASIC - events.py
Input event loop and handlers for BASIC events

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import time
import Queue
from contextlib import contextmanager

import error
import signals

import config
import state
import timedate
import scancode


###############################################################################
# initialisation

def prepare():
    """ Initialise events module. """
    global num_fn_keys
    if config.get('syntax') == 'tandy':
        num_fn_keys = 12
    else:
        num_fn_keys = 10


###############################################################################
# main event checker

tick_s = 0.0001
longtick_s = 0.006 - tick_s


def wait(suppress_events=False):
    """ Wait and check events. """
    time.sleep(longtick_s)
    if not suppress_events:
        check_events()

def check_events():
    """ Main event cycle. """
    time.sleep(tick_s)
    check_input()
    if state.session.parser.run_mode:
        state.session.parser.events.check()
    state.console_state.keyb.drain_event_buffer()

def check_input():
    """ Handle input events. """
    while True:
        try:
            signal = signals.input_queue.get(False)
        except Queue.Empty:
            if not state.console_state.keyb.pause:
                break
            else:
                time.sleep(tick_s)
                continue
        # we're on it
        signals.input_queue.task_done()
        if signal.event_type == signals.KEYB_QUIT:
            raise error.Exit()
        if signal.event_type == signals.KEYB_CLOSED:
            state.console_state.keyb.close_input()
        elif signal.event_type == signals.KEYB_CHAR:
            # params is a unicode sequence
            state.console_state.keyb.insert_chars(*signal.params)
        elif signal.event_type == signals.KEYB_DOWN:
            # params is e-ASCII/unicode character sequence, scancode, modifier
            state.console_state.keyb.key_down(*signal.params)
        elif signal.event_type == signals.KEYB_UP:
            state.console_state.keyb.key_up(*signal.params)
        elif signal.event_type == signals.PEN_DOWN:
            state.console_state.pen.down(*signal.params)
        elif signal.event_type == signals.PEN_UP:
            state.console_state.pen.up()
        elif signal.event_type == signals.PEN_MOVED:
            state.console_state.pen.moved(*signal.params)
        elif signal.event_type == signals.STICK_DOWN:
            state.console_state.stick.down(*signal.params)
        elif signal.event_type == signals.STICK_UP:
            state.console_state.stick.up(*signal.params)
        elif signal.event_type == signals.STICK_MOVED:
            state.console_state.stick.moved(*signal.params)
        elif signal.event_type == signals.CLIP_PASTE:
            state.console_state.keyb.insert_chars(*signal.params, check_full=False)
        elif signal.event_type == signals.CLIP_COPY:
            text = state.console_state.screen.get_text(*(signal.params[:4]))
            signals.video_queue.put(signals.Event(
                    signals.VIDEO_SET_CLIPBOARD_TEXT, (text, signal.params[-1])))


###############################################################################
# BASIC event triggers

# 12 definable function keys for Tandy
num_fn_keys = 10


class EventHandler(object):
    """ Manage event triggers. """

    def __init__(self):
        """ Initialise untriggered and disabled. """
        self.reset()

    def reset(self):
        """ Reset to untriggered and disabled initial state. """
        self.gosub = None
        self.enabled = False
        self.stopped = False
        self.triggered = False

    def set_jump(self, jump):
        """ Set the jump line number. """
        self.gosub = jump

    def command(self, command_char):
        """ Turn the event ON, OFF and STOP. """
        if command_char == '\x95':
            # ON
            self.enabled = True
            self.stopped = False
        elif command_char == '\xDD':
            # OFF
            self.enabled = False
        elif command_char == '\x90':
            # STOP
            self.stopped = True
        else:
            return False
        return True

    def trigger(self):
        """ Trigger the event. """
        self.triggered = True

    def check(self):
        """ Stub for event checker. """


class PlayHandler(EventHandler):
    """ Manage PLAY (music queue) events. """

    def __init__(self):
        """ Initialise PLAY trigger. """
        EventHandler.__init__(self)
        self.last = [0, 0, 0]
        self.trig = 1
        self.multivoice = config.get('syntax') in ('pcjr', 'tandy')

    def check(self):
        """ Check and trigger PLAY (music queue) events. """
        play_now = [state.console_state.sound.queue_length(voice) for voice in range(3)]
        if self.multivoice:
            for voice in range(3):
                if (play_now[voice] <= self.trig and
                        play_now[voice] > 0 and
                        play_now[voice] != self.last[voice]):
                    self.trigger()
        else:
            if (self.last[0] >= self.trig and
                    play_now[0] < self.trig):
                self.trigger()
        self.last = play_now

    def set_trigger(self, n):
        """ Set PLAY trigger to n notes. """
        self.trig = n


class TimerHandler(EventHandler):
    """ Manage TIMER events. """

    def __init__(self):
        """ Initialise TIMER trigger. """
        EventHandler.__init__(self)
        self.period = 0
        self.start = 0

    def set_trigger(self, n):
        """ Set TIMER trigger to n milliseconds. """
        self.period = n

    def check(self):
        """ Trigger TIMER events. """
        mutimer = timedate.timer_milliseconds()
        if mutimer >= self.start + self.period:
            self.start = mutimer
            self.trigger()


class ComHandler(EventHandler):
    """ Manage COM-port events. """

    def __init__(self, port):
        """ Initialise COM trigger. """
        EventHandler.__init__(self)
        # devices aren't initialised at this time so just keep the name
        self.portname = ('COM1:', 'COM2:')[port]

    def check(self):
        """ Trigger COM-port events. """
        if (state.io_state.devices[self.portname] and
                    state.io_state.devices[self.portname].char_waiting()):
            self.trigger()


class KeyHandler(EventHandler):
    """ Manage KEY events. """

    def __init__(self, scancode=None):
        """ Initialise KEY trigger. """
        EventHandler.__init__(self)
        self.modcode = None
        self.scancode = scancode
        self.predefined = (scancode is not None)

    def check(self):
        """ Trigger KEY events. """
        if self.scancode is None:
            return False
        for c, scancode, modifiers, check_full in state.console_state.keyb.prebuf:
            if scancode != self.scancode:
                continue
            # build KEY trigger code
            # see http://www.petesqbsite.com/sections/tutorials/tuts/keysdet.txt
            # second byte is scan code; first byte
            #  0       if the key is pressed alone
            #  1 to 3    if any Shift and the key are combined
            #    4       if Ctrl and the key are combined
            #    8       if Alt and the key are combined
            #   32       if NumLock is activated
            #   64       if CapsLock is activated
            #  128       if we are defining some extended key
            # extended keys are for example the arrow keys on the non-numerical keyboard
            # presumably all the keys in the middle region of a standard PC keyboard?
            #
            # for predefined keys, modifier is ignored
            # from modifiers, exclude scroll lock at 0x10 and insert 0x80.
            if (self.predefined) or (modifiers is None or self.modcode == modifiers & 0x6f):
                # trigger event
                self.trigger()
                # drop key from key buffer
                if self.enabled:
                    state.console_state.keyb.prebuf.remove((c, scancode, modifiers, check_full))
                    return True
        return False

    def set_trigger(self, keystr):
        """ Set KEY trigger to chr(modcode)+chr(scancode). """
        # can't redefine scancodes for predefined keys 1-14 (pc) 1-16 (tandy)
        if not self.predefined:
            self.modcode = ord(keystr[0])
            self.scancode = ord(keystr[1])


class PenHandler(EventHandler):
    """ Manage PEN events. """

    def check(self):
        """ Trigger PEN events. """
        if state.console_state.pen.poll_event():
            self.trigger()


class StrigHandler(EventHandler):
    """ Manage STRIG events. """

    def __init__(self, joy, button):
        """ Initialise STRIG trigger. """
        EventHandler.__init__(self)
        self.joy = joy
        self.button = button

    def check(self):
        """ Trigger STRIG events. """
        if state.console_state.stick.poll_event(self.joy, self.button):
            self.trigger()


class Events(object):
    """ Event management. """

    def __init__(self):
        """ Initialise event triggers. """
        self.reset()

    def reset(self):
        """ Initialise or reset event triggers. """
        # KEY: init key events
        keys = [
            scancode.F1, scancode.F2, scancode.F3, scancode.F4, scancode.F5,
            scancode.F6, scancode.F7, scancode.F8, scancode.F9, scancode.F10]
        if num_fn_keys == 12:
            # Tandy only
            keys += [scancode.F11, scancode.F12]
        keys += [scancode.UP, scancode.LEFT, scancode.RIGHT, scancode.DOWN]
        keys += [None] * (20 - num_fn_keys - 4)
        self.key = [KeyHandler(sc) for sc in keys]
        # other events
        self.timer = TimerHandler()
        self.play = PlayHandler()
        self.com = [ComHandler(0), ComHandler(1)]
        self.pen = PenHandler()
        # joy*2 + button
        self.strig = [StrigHandler(joy, button)
                      for joy in range(2) for button in range(2)]
        # all handlers in order of handling; TIMER first
        # key events are not handled FIFO but first 11-20 in that order, then 1-10
        self.all = ([self.timer]
            + [self.key[num] for num in (range(10, 20) + range(10))]
            + [self.play] + self.com + [self.pen] + self.strig)
        # set suspension off
        self.suspend_all = False

    def check(self):
        """ Check events. """
        for e in self.all:
            e.check()

    @contextmanager
    def suspend(self):
        """ Context guard to suspend events. """
        self.suspend_all, store = True, self.suspend_all
        yield
        self.suspend_all = store


###############################################################################

prepare()
