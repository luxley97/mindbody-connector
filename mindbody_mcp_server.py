"""
Mindbody MCP 连接器 — v0.1 骨架（Demo 用，未联调）

用途：让 AI 助手通过 4 个标准动作操作 Mindbody 门店的预约：
    search_services / check_availability / book_appointment / cancel_appointment

状态：骨架已写好结构、鉴权、写保护开关与错误处理；端点和参数名已按公开 SDK 核对，
      但尚未在 sandbox 实测。第一次跑通 sandbox 时需要核对的地方都用 TODO 标出。

安装依赖：
    pip install "mcp[cli]" httpx
    （代码同时兼容 mcp 1.x 与 2.x，无需锁定版本）

运行（MCP stdio 模式，供 Claude Desktop / 其他 MCP 客户端调用）：
    python mindbody_mcp_server.py

离线冒烟测试（不需要任何凭证，返回假数据）：
    MINDBODY_MOCK=1 python mindbody_mcp_server.py

安全设计（两把锁）：
    MINDBODY_ALLOW_BOOKINGS=true   才允许下单（默认 false）
    MINDBODY_ALLOW_CANCEL=true     才允许取消（默认 false）
    —— 默认状态下 AI 只能"看"，不能"动"。给商家演示时先讲这个。
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

try:  # mcp >= 2.0：FastMCP 已更名为 MCPServer
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # mcp < 2.0：沿用旧名字
    from mcp.server.fastmcp import FastMCP as _MCPServer

# ---------------------------------------------------------------- 配置

BASE_URL = "https://api.mindbodyonline.com/public/v6"

API_KEY = os.getenv("MINDBODY_API_KEY", "")
SITE_ID = os.getenv("MINDBODY_SITE_ID", "-99")          # -99 = 官方 sandbox 站点
SOURCE_NAME = os.getenv("MINDBODY_SOURCE_NAME", "AgentBookingConnector")
STAFF_USERNAME = os.getenv("MINDBODY_USERNAME", "Siteowner")
STAFF_PASSWORD = os.getenv("MINDBODY_PASSWORD", "")
MOCK = os.getenv("MINDBODY_MOCK", "0") == "1"

ALLOW_BOOKINGS = os.getenv("MINDBODY_ALLOW_BOOKINGS", "false").lower() == "true"
ALLOW_CANCEL = os.getenv("MINDBODY_ALLOW_CANCEL", "false").lower() == "true"

TIMEOUT = httpx.Timeout(20.0, connect=10.0)

mcp = _MCPServer("mindbody-connector")

_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}

# ---------------------------------------------------------------- 基础工具


def _base_headers() -> dict[str, str]:
    return {
        "Api-Key": API_KEY,
        "SiteId": str(SITE_ID),
        "SourceName": SOURCE_NAME,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _staff_token() -> str:
    """获取员工用户令牌。写操作必需；有效期约 60 分钟，这里缓存 55 分钟。"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return str(_token_cache["token"])
    if MOCK:
        _token_cache.update(token="mock-token", expires_at=now + 3300)
        return "mock-token"
    # TODO 联调核对：官方门户 "Use Free Sandbox" 页给出的沙盒站点凭据是
    #   Username = "mindbodysandboxsite@gmail.com" / Password = "Apitest1234"（注意 A 大写）。
    #   早年文档另有 Username = "Siteowner" / Password = "apitest1234" 的写法，可作备选。
    #   正式接入应改为 Partner OAuth 流程（参考官方仓库 mindbody/PartnerOAuthWebApp）
    resp = httpx.post(
        f"{BASE_URL}/usertoken/issue",
        headers=_base_headers(),
        json={"Username": STAFF_USERNAME, "Password": STAFF_PASSWORD},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    token = resp.json()["AccessToken"]
    _token_cache.update(token=token, expires_at=now + 3300)
    return str(token)


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if MOCK:
        return _mock_response(path, params)
    resp = httpx.get(
        f"{BASE_URL}{path}", headers=_base_headers(), params=params, timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if MOCK:
        return _mock_response(path, payload)
    headers = _base_headers()
    headers["Authorization"] = _staff_token()
    resp = httpx.post(f"{BASE_URL}{path}", headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _mock_response(path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """离线假数据：仅用于验证 MCP 服务能正常启动、工具能被调用。"""
    if path.endswith("/site/services"):
        return {
            "Services": [
                {"Id": 1, "Name": "60-min Deep Tissue Massage"},
                {"Id": 2, "Name": "Signature Facial"},
                {"Id": 3, "Name": "Reformer Pilates — 1:1"},
            ]
        }
    if path.endswith("/appointment/bookableitems"):
        return {
            "Availabilities": [
                {
                    "StartDateTime": "2026-10-15T10:00:00",
                    "EndDateTime": "2026-10-15T11:00:00",
                    "StaffId": 11,
                    "SessionTypeId": 1,
                    "BookableItem": {"Name": "60-min Deep Tissue Massage"},
                }
            ]
        }
    if path.endswith("/appointment/addappointment"):
        return {"Appointment": {"Id": 987654, "Status": "Booked"}}
    if path.endswith("/appointment/updateappointment"):
        return {
            "Appointment": {
                "Id": (payload or {}).get("AppointmentId", 987654),
                "Status": "Cancelled",
            }
        }
    if path.endswith("/usertoken/issue"):
        return {"AccessToken": "mock-token", "TokenType": "Bearer"}
    return {}


# ---------------------------------------------------------------- MCP 工具（4 个动作）


@mcp.tool()
def search_services(query: str = "", limit: int = 20) -> dict[str, Any]:
    """查找门店提供的服务项目（美甲/按摩/课程等）。query 为可选关键词，留空返回全部。"""
    data = _get("/site/services", {"Limit": limit})
    services = data.get("Services", [])
    if query:
        q = query.lower()
        services = [s for s in services if q in str(s.get("Name", "")).lower()]
    return {
        "count": len(services),
        "services": [
            {"id": s.get("Id"), "name": s.get("Name")} for s in services[:limit]
        ],
    }


@mcp.tool()
def check_availability(
    start_date: str,
    end_date: str,
    session_type_ids: list[int] | None = None,
    staff_ids: list[int] | None = None,
) -> dict[str, Any]:
    """查询某时间段内可预约的空闲时段。

    start_date / end_date 格式：YYYY-MM-DD。
    返回的每条 Availabilities 都可以直接用于 book_appointment。
    """
    params: dict[str, Any] = {"StartDate": start_date, "EndDate": end_date}
    if session_type_ids:
        params["SessionTypeIds"] = ",".join(str(i) for i in session_type_ids)
    if staff_ids:
        params["StaffIds"] = ",".join(str(i) for i in staff_ids)
    # TODO 联调核对：bookableitems 的参数名（StartDate / EndDate）以官方 API Reference 为准
    data = _get("/appointment/bookableitems", params)
    slots = data.get("Availabilities", [])
    return {
        "count": len(slots),
        "slots": [
            {
                "start": s.get("StartDateTime"),
                "end": s.get("EndDateTime"),
                "staff_id": s.get("StaffId"),
                "session_type_id": s.get("SessionTypeId"),
                "name": (s.get("BookableItem") or {}).get("Name"),
            }
            for s in slots[:20]
        ],
    }


@mcp.tool()
def book_appointment(
    start_datetime: str,
    session_type_id: int,
    staff_id: int,
    client_id: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """为顾客预约一个时段。写操作 —— 需商家显式授权，且服务端开关已打开。

    start_datetime 格式：YYYY-MM-DDTHH:MM:SS
    """
    if not ALLOW_BOOKINGS:
        return {
            "error": "booking_disabled",
            "hint": "写操作默认关闭。确认商家已授权后，设置环境变量 MINDBODY_ALLOW_BOOKINGS=true 再重启服务。",
        }
    payload: dict[str, Any] = {
        "StartDateTime": start_datetime,
        "SessionTypeId": session_type_id,
        "StaffId": staff_id,
        "Execute": "confirm",
        "SendEmail": False,
        "Test": False,
    }
    if client_id:
        payload["ClientId"] = client_id
    if notes:
        payload["Notes"] = notes
    data = _post("/appointment/addappointment", payload)
    appt = data.get("Appointment", {})
    return {
        "appointment_id": appt.get("Id"),
        "status": appt.get("Status"),
        "start": appt.get("StartDateTime"),
    }


@mcp.tool()
def cancel_appointment(appointment_id: int, send_email: bool = False) -> dict[str, Any]:
    """取消一个已有预约。写操作 —— 需商家显式授权，且服务端开关已打开。"""
    if not ALLOW_CANCEL:
        return {
            "error": "cancel_disabled",
            "hint": "取消操作默认关闭。确认商家已授权后，设置环境变量 MINDBODY_ALLOW_CANCEL=true 再重启服务。",
        }
    payload = {
        "AppointmentId": appointment_id,
        "Execute": "cancel",  # 官方支持的取值：confirm / unconfirm / arrive / unarrive / cancel / latecancel / complete
        "SendEmail": send_email,
    }
    data = _post("/appointment/updateappointment", payload)
    appt = data.get("Appointment", {})
    return {"appointment_id": appt.get("Id"), "status": appt.get("Status")}


# ---------------------------------------------------------------- 启动

if __name__ == "__main__":
    mcp.run()
