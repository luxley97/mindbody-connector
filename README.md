# Demo 运行说明（5 分钟上手）

本目录是《Mindbody MCP 连接器》的最小验证 Demo，目的是：**一周内让 AI 助手能在 sandbox 沙盒里完成一次真实预约**，并把过程录成 30–60 秒的演示素材用于验证需求。

---

## 0. 本机状态：已就绪 ✅

这台电脑上环境**已经装好并实测通过**（Python 3.13 + `mcp` + `httpx`），无需再安装任何东西。

- Python 解释器：`C:\Users\luxle\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
- 已验证：7 项结构自检全部通过 + 真实 MCP 协议握手成功（服务启动、4 个工具可被发现、只读查询返回数据、写操作被默认拦截）

自己重跑一遍验证：

```
cd "C:\Users\luxle\WorkBuddy\2026-10-08-21-46-57\mindbody-pilot\demo"
$env:MINDBODY_MOCK="1"
C:\Users\luxle\.workbuddy\binaries\python\envs\default\Scripts\python.exe smoke_test.py
```

最后一行打印 `全部通过` 即正常。**这一步不联网、不需要 API Key、不花钱，随时可重跑。**

---

## 1. 换一台机器时的依赖安装

```
pip install "mcp[cli]" httpx
```

代码同时兼容 `mcp` 1.x 与 2.x，**不需要锁定版本**（2.x 中 `FastMCP` 已更名为 `MCPServer`，代码顶部做了自动适配）。

---

## 2. 离线冒烟测试（不需要任何凭证）

```
MINDBODY_MOCK=1 python smoke_test.py     # 结构化自检，7 项逐条打印 OK/FAIL
MINDBODY_MOCK=1 python mindbody_mcp_server.py   # 以 stdio 模式启动服务，Ctrl+C 退出
```

第二种方式启动后会"停住"不输出，这是**正常的**——它在等待 MCP 客户端连接，不是卡死。

---

## 3. 接上 Mindbody sandbox（账号已注册，凭证见 `../凭证记录-勿上传GitHub.txt`）

官方门户 "Use Free Sandbox" 页给出的沙盒值：`Studio Id = -99`、`User Name = mindbodysandboxsite@gmail.com`、`Password = Apitest1234`。

```
export MINDBODY_API_KEY="门户 Account → API Credentials → API Keys 里创建的 Key"
export MINDBODY_SITE_ID="-99"                              # 官方沙盒站点
export MINDBODY_SOURCE_NAME="Luxley"                       # 门户给出的 Source name
export MINDBODY_USERNAME="mindbodysandboxsite@gmail.com"   # 沙盒站点登录名
export MINDBODY_PASSWORD="Apitest1234"                     # 注意 A 大写
python mindbody_mcp_server.py
```

沙盒数据每晚 12:00 AM PST 自动重置，测试写坏了不用处理。

3. 关掉写保护做一次真实预约测试：

```
export MINDBODY_ALLOW_BOOKINGS="true"
export MINDBODY_ALLOW_CANCEL="true"
```

> Windows PowerShell 写法：把 `export X="Y"` 换成 `$env:X="Y"`。

---

## 4. 接到 Claude Desktop 测试

在 Claude Desktop 的 MCP 配置里加入：

```json
{
  "mcpServers": {
    "mindbody": {
      "command": "C:\\Users\\luxle\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe",
      "args": ["C:\\Users\\luxle\\WorkBuddy\\2026-10-08-21-46-57\\mindbody-pilot\\demo\\mindbody_mcp_server.py"],
      "env": {
        "MINDBODY_API_KEY": "...",
        "MINDBODY_SITE_ID": "-99",
        "MINDBODY_ALLOW_BOOKINGS": "false",
        "MINDBODY_ALLOW_CANCEL": "false"
      }
    }
  }
}
```

然后在对话里说："帮我查一下这家店有什么服务，再找下周二的空闲时段"。能看到返回结果即算成功。

---

## 5. 已知待联调项（首次跑 sandbox 时逐条核对打勾）

- [ ] `GET /site/services` 的返回字段名是否为 `Services`
- [ ] `GET /appointment/bookableitems` 的参数名（StartDate / EndDate）与返回字段
- [ ] `POST /appointment/addappointment` 的必填字段（ClientId 是否必传）
- [ ] `POST /appointment/updateappointment` 取消后返回的 Status 值
- [ ] 员工用户令牌 `POST /usertoken/issue` 在 sandbox 的可用性
      （官方门户 "Use Free Sandbox" 页给出的沙盒站点凭据：
      `Username=mindbodysandboxsite@gmail.com` / `Password=Apitest1234`（**A 大写**）。
      早年文档另有 `Siteowner` / `apitest1234` 的写法，可作备选）

代码里对应的位置都写了 `# TODO 联调核对:` 注释，搜这个关键词可以直接定位。

---

## 6. 安全红线（演示时要展示给商家看的设计）

- 写操作（下单/取消）默认关闭，需要服务端环境变量显式打开
- 下单与取消是**两个独立开关**，避免"开了下单就顺带能取消"
- 所有凭证只存在于服务端环境变量，绝不写进代码或前端
- `凭证记录-勿上传GitHub.txt` 永远不要提交进仓库

---

## 文件清单

| 文件 | 用途 |
|---|---|
| `mindbody_mcp_server.py` | MCP 服务主体，4 个工具 |
| `smoke_test.py` | 离线自检，7 项检查，无需凭证 |
| `demo_walkthrough.py` | 录屏专用自动演示剧本（约 55 秒），无需凭证；`--fast` 快速自检 |
| `README.md` | 本文件 |

---

## 7. 录制演示视频（30–60 秒素材）

```
cd "C:\Users\luxle\WorkBuddy\2026-10-08-21-46-57\mindbody-pilot\demo"
C:\Users\luxle\.workbuddy\binaries\python\envs\default\Scripts\python.exe demo_walkthrough.py
```

录制：终端窗口放大、字体调大（Ctrl+滚轮）→ `Win + Alt + R` 开始 → 播完再按一次停止 →
视频在 `C:\Users\luxle\Videos\Captures`。不需要任何凭证、不联网。
