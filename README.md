# Codex Cloud LabVIEW 2025 MCP

Windows 11 / LabVIEW 2025 Q3 64-bit 的設定、安裝輔助工具、工作區 Skills 與 MCP 測試橋接。此專案保存可審閱的設定與腳本；它不是完整 VM 映像或一鍵還原工具。

## 已驗證狀態

- Windows 11 曾以 QEMU TCG `max,vendor=GenuineIntel,pmu=off` 正常進入桌面；此設定避開已觀察到的 RDPMC 當機路徑。
- LabVIEW Evaluation Version 2025 Q3 (64-bit) 25.3f0 曾啟動；七天評估版已開始計時。
- Zuehlke LabVIEW MCP 2.3.1：透過私有 HTTP 至 stdio 橋接，initialize、tools/list、pylv_status 與 lvai_list_labview_installations 成功。建立或執行 VI、ChatGPT 原生連接尚未驗證。
- JanGoebel/labview_assistant 仍缺 MCP SDK、IG HTTP Utils 與 JSONtext；SDK 版本須確認與 LabVIEW 25.3 相容。

## 內容與還原前提

`vm/` 保存原 VM 啟動與 QMP 工具，含原機器 `/workspace/windows-vm` 等絕對路徑，須先依新主機位置調整。需自行準備 Windows 11 授權與媒體、LabVIEW 2025 Q3 64-bit 授權或有效評估版、QEMU、OVMF、swtpm 和磁碟空間。目前紀錄使用 TCG；支援 KVM 的 Linux 主機可改善效能。

`guest/` 保存安裝與啟動腳本，假設 host 白名單 HTTP helper 在 127.0.0.1:8765，guest 透過 10.0.2.2:8765 取得固定版本 release 與 bridge；可使用 `guest/transfer-server.py`，先核對其中檔案路徑並依原環境部署。腳本驗證 release SHA-256，不啟用自動更新。

`bridge/` 是私人本機 HTTP 至 MCP stdio 橋接及假後端測試；QEMU 轉發應只綁主機 127.0.0.1，並限制客體防火牆來源。ChatGPT 自訂 MCP 的公開 HTTPS、認證與註冊需另外設計與驗證。

`.agents/skills/` 含三個工作區適配 Skills，其中 Zühlke 參考工作流程保留 MIT 授權。其他候選與相容性見 [docs/candidates.md](docs/candidates.md)。

執行 `python bridge/test_mcp_stdio_http.py` 測試橋接。該測試使用假後端，不代表 LabVIEW VI 建立／執行已成功。

虛擬磁碟、TPM、ISO、個人資料、存取權杖、安裝日誌及大型第三方二進位檔不包含於儲存庫，因此無法還原當前 VM 的實際磁碟內容、啟用狀態或快照。固定版及 SHA-256 見 [release provenance](docs/release-provenance.json)。
