# LabVIEW 2025 Q3 自動化方案與安裝紀錄

| 項目 | 用途／適用性 | 本次處理 |
|---|---|---|
| 工作區 Skills（3個） | VI 開發、MCP 操作、慢速 VM 操作 | 已安裝於 /workspace/.agents/skills；本地適配版，非 ChatGPT 商店插件 |
| Zuehlke/labview-mcp v2.3.1 | Windows x64 MCP；2025 採 pylabview／ActiveX，需實測可用範圍 | 已下載並驗證官方 SHA-256，開始 guest 安裝；尚未宣稱連線成功 |
| Zuehlke 上游工作流程（8份） | VI 新建／編輯、文件、類別、DQMH、三種測試框架 | 已下載審閱；選取 generator/editor/doc 作為 Skills 參考，保留 MIT 授權 |
| JanGoebel/labview_assistant | LabVIEW 原生 HTTP MCP，可做 VI Scripting | 保留既有專案；外部 SDK／IG／JSONtext 相依尚未解決 |
| labview-native-mcp | Python COM／VI Scripting，較小 | 已下載評估；上游僅驗證 2021／2018，不直接當作 2025 已相容 |
| JorgenSteen/labview-mcp-skills | 現成 Claude Skill，Actor Framework 工作流程 | 版本與授權尚未確認適合，不安裝到啟用路徑 |
| ChatGPT 插件目錄 | 尋找可直接連接的 LabVIEW 專用插件 | 本次搜尋未找到已確認適合的專用項目；不安裝無關插件 |

來源：
- https://github.com/Zuehlke/labview-mcp （MIT）
- https://github.com/JanGoebel/labview_assistant
- https://github.com/chinayuren2022-2025/labview-native-mcp （MIT）
- https://github.com/JorgenSteen/labview-mcp-skills

Zuehlke release v2.3.1 SHA-256：`34cffee146e3452dc391cbf6b2c3c2d2c079e3a63e72796c4770c39217cc3224`。
未啟用自動更新。原始文件中 2026 AI/gRPC 的條件與舊版 ActiveX 路徑存在文字差異，因此必須以實際工具回應和 VI 測試判定。

技能：`skills-installation.json`。下載來源／雜湊：`downloads/*provenance.json`。
客體安裝進度會回傳到 `/workspace/windows-vm/diagnostics/cpu-test/transfer/guest-automation-state.json`。
本地 HTTP-to-stdio bridge 位於 `bridge/`，已用假後端驗證協定、並行 ID、逾時後續回應與來源限制；這不等於 LabVIEW 端已通過測試，也不等於 ChatGPT 商店已連接。
