# -*- coding: utf-8 -*-
"""
Screen-recording demo script (demo_walkthrough.py)
==================================================
Plays a scripted ~55-second walkthrough of an AI assistant booking an
appointment at a Mindbody business through this connector. Just screen-record
the terminal while it runs. No credentials or network required.

Usage:
    python demo_walkthrough.py          # normal speed (~55 s, for recording)
    python demo_walkthrough.py --fast   # quick self-check (no pauses)

Recording (built into Windows, nothing to install):
    1. Maximize the terminal window and enlarge the font (Ctrl + mouse wheel)
    2. Press Win + Alt + R to start recording, press again to stop
    3. The video is saved to C:\\Users\\<you>\\Videos\\Captures
"""
import sys
import time

FAST = "--fast" in sys.argv
PAUSE = 0.05 if FAST else 0.9      # pause between steps (seconds)
TYPE = 0.001 if FAST else 0.035    # typewriter delay per character (seconds)


def say(text, color=None, delay=PAUSE, typewriter=False):
    prefix = {"user": "\033[96m", "tool": "\033[93m",
              "ok": "\033[92m", "warn": "\033[91m",
              "note": "\033[90m"}.get(color, "")
    end = "\033[0m" if prefix else ""
    if typewriter:
        for ch in text:
            print(prefix + ch + end, end="", flush=True)
            time.sleep(TYPE)
        print()
    else:
        print(prefix + text + end)
    time.sleep(delay)


def main():
    print()
    say("=" * 56, "note", 0.3)
    say("  Mindbody Connector - AI Agent Booking Demo (sandbox)", "note", 1.2)
    say("=" * 56, "note", 1.5)
    print()

    say("Consumer: I'd like a 60-minute deep tissue massage tomorrow",
        "user", 0.3, typewriter=True)
    say("          afternoon. What time slots are available?", "user", 1.8, typewriter=True)

    say('-> [tool] search_services(service_type="massage")', "tool", 1.0)
    say("   Found: 60-min Deep Tissue Massage - $89 - Serenity Spa", "note", 1.2)
    say('-> [tool] check_availability(service_id=101, date=tomorrow)', "tool", 1.0)
    say("   Available: 1:00 PM / 2:00 PM / 4:30 PM", "note", 1.6)

    say("Consumer: Book the 2:00 PM slot, please.", "user", 1.6, typewriter=True)

    say("-> [tool] book_appointment(...)", "tool", 0.8)
    say("   X booking_disabled - writes are OFF by default; merchant has not opted in yet",
        "warn", 2.0)

    say("   [narration] The merchant flips one switch in Mindbody to authorize...",
        "note", 2.2)

    say("-> [tool] book_appointment(...)   # switch now ON", "tool", 0.8)
    say("   OK appointment_id=987654 - status=Booked - tomorrow 2:00 PM", "ok", 1.8)

    say("Consumer: Something came up. Please cancel it.", "user", 1.6, typewriter=True)

    say("-> [tool] cancel_appointment(appointment_id=987654)", "tool", 0.8)
    say("   OK status=Cancelled", "ok", 1.8)

    print()
    say("Key point: reads work out of the box; writes (book/cancel) sit behind", "note", 0.6)
    say("two separate switches, OFF by default and enabled per site -", "note", 0.6)
    say("the merchant always stays in control.", "note", 2.5)
    say("- end of demo (sandbox environment, no real business data) -", "note", 1.0)


if __name__ == "__main__":
    main()
