# -*- coding: utf-8 -*-
"""
录屏专用演示脚本（demo_walkthrough.py）
========================================
用途：录制 30-60 秒演示视频。运行后自动播放一个"AI 助手通过 Mindbody 连接器
预约门店"的完整剧本，含打字机效果和停顿，直接对着它录屏即可。

用法：
    python demo_walkthrough.py          # 正常速度（约 55 秒）
    python demo_walkthrough.py --fast   # 快速自检（不等停顿）

录制方法（Windows 自带，无需装软件）：
    1. 把这个终端窗口拉大到全屏，字体调大（Ctrl + 滚轮）
    2. 按 Win + Alt + R 开始录制，再按一次停止
    3. 视频自动保存到 C:\\Users\\<你>\\Videos\\Captures
"""
import sys
import time

FAST = "--fast" in sys.argv
PAUSE = 0.05 if FAST else 0.9      # 每步之间的停顿（秒）
TYPE = 0.001 if FAST else 0.035    # 打字机每字间隔（秒）


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
    say("  Mindbody Connector — AI Agent Booking Demo (sandbox)", "note", 1.2)
    say("=" * 56, "note", 1.5)
    print()

    say("消费者：明天下午想做 60 分钟的深层组织按摩，帮我看看有什么时段？",
        "user", 1.8, typewriter=True)

    say("→ [tool] search_services(service_type=\"massage\")", "tool", 1.0)
    say("  找到：60-min Deep Tissue Massage · $89 · Serenity Spa", "note", 1.2)
    say("→ [tool] check_availability(service_id=101, date=明天)", "tool", 1.0)
    say("  空闲时段：13:00 / 14:00 / 16:30", "note", 1.6)

    say("消费者：订 14:00 那个。", "user", 1.6, typewriter=True)

    say("→ [tool] book_appointment(...)", "tool", 0.8)
    say("  ✗ booking_disabled —— 写操作默认关闭，商家尚未授权", "warn", 2.0)

    say("  [旁白] 商家在 Mindbody 后台一键授权后，写保护开关打开……", "note", 2.2)

    say("→ [tool] book_appointment(...)  # 开关已打开", "tool", 0.8)
    say("  ✓ appointment_id=987654 · status=Booked · 明天 14:00", "ok", 1.8)

    say("消费者：临时有事，帮我取消。", "user", 1.6, typewriter=True)

    say("→ [tool] cancel_appointment(appointment_id=987654)", "tool", 0.8)
    say("  ✓ status=Cancelled", "ok", 1.8)

    print()
    say("要点：读操作开箱即用；写操作（预约/取消）双重开关保护，", "note", 0.6)
    say("默认关闭、按门店授权 —— 商家始终握有控制权。", "note", 2.5)
    say("— demo 结束（沙盒环境，无真实门店数据）—", "note", 1.0)


if __name__ == "__main__":
    main()
