"""
离线自检脚本 —— 不需要任何 API Key，验证 MCP 服务能否正常加载、4 个工具是否可用、写保护是否生效。

运行：
    MINDBODY_MOCK=1 python smoke_test.py

预期输出：6 项全部 OK，最后打印 "全部通过"。
"""

from __future__ import annotations

import asyncio
import os
import sys

os.environ.setdefault("MINDBODY_MOCK", "1")

import mindbody_mcp_server as s  # noqa: E402

PASS = 0
FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    mark = "OK  " if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"[{mark}] {label}" + (f" -> {detail}" if detail else ""))


# --- T1 只读：查服务项目 ---------------------------------------------------
r1 = s.search_services("massage")
check("T1 search_services", r1.get("count", 0) >= 1, f"{r1.get('count')} 条，首条={r1['services'][0]['name'] if r1.get('services') else '无'}")

# --- T2 只读：查空闲时段 ---------------------------------------------------
r2 = s.check_availability("2026-10-15", "2026-10-16")
check("T2 check_availability", r2.get("count", 0) >= 1, f"{r2.get('count')} 个时段")

# --- T3 写保护：开关关闭时下单必须被拒 -------------------------------------
r3 = s.book_appointment("2026-10-15T10:00:00", 1, 11)
check("T3 写保护(下单)默认拦截", r3.get("error") == "booking_disabled", str(r3.get("error")))

# --- T3b 写保护：开关关闭时取消必须被拒 ------------------------------------
r3b = s.cancel_appointment(987654)
check("T3b 写保护(取消)默认拦截", r3b.get("error") == "cancel_disabled", str(r3b.get("error")))

# --- T4 显式打开开关后，下单成功 -------------------------------------------
s.ALLOW_BOOKINGS = True
s.ALLOW_CANCEL = True
r4 = s.book_appointment("2026-10-15T10:00:00", 1, 11, notes="self-test")
check("T4 开关打开后下单", r4.get("appointment_id") == 987654, f"appointment_id={r4.get('appointment_id')}, status={r4.get('status')}")

# --- T5 取消成功 -----------------------------------------------------------
r5 = s.cancel_appointment(987654)
check("T5 开关打开后取消", r5.get("status") == "Cancelled", f"status={r5.get('status')}")

# --- T6 MCP 工具已注册 -----------------------------------------------------
names: list[str] = []
try:
    tools = asyncio.run(s.mcp.list_tools())
    names = [getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else str(t)) for t in tools]
except Exception:  # 兼容不同 mcp 版本
    for attr in ("_tools", "_tool_manager", "_tool_handlers"):
        obj = getattr(s.mcp, attr, None)
        if isinstance(obj, dict) and obj:
            names = list(obj.keys())
            break
        if obj is not None and hasattr(obj, "list_tools"):
            names = [t.name for t in obj.list_tools()]
            break

expected = {"search_services", "check_availability", "book_appointment", "cancel_appointment"}
check("T6 四个工具已注册", expected.issubset(set(names)), f"{sorted(names)}")

print()
print(f"结果：{PASS} 通过 / {FAIL} 失败")
if FAIL:
    sys.exit(1)
print("全部通过 —— MCP 服务结构正常，可以进入 sandbox 联调。")
