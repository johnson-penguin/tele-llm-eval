# TeleQnA 評測腳本優化報告 (Optimization Report)

## 1. 摘要 (Executive Summary)
本報告旨在分析與比較 `run.py` 的優化版本與原始版本 (`TeleQnA/run.py`) 之間的差異。
此次代碼重構的主要目標為 **適配本地端大型語言模型 (Local LLM Adaptation)**，並顯著提升評測過程的 **穩定性 (Stability)**、**可觀察性 (Observability)** 與 **開發效率 (Developer Experience)**。

## 2. 環境適配與配置 (Configuration & Adaptation)

為了支援地端部署的開源模型 (如 QwQ-32b)，我們對環境配置進行了關鍵調整。

| 比較項目 | 原始版本 (Baseline) | 優化版本 (Optimized) | 技術意涵 |
| :--- | :--- | :--- | :--- |
| **目標模型** | `gpt-3.5-turbo` | `log-copilot` (Local) | 從雲端 API 遷移至本地部署模型，大幅降低 token 成本並確保資料隱私。 |
| **API 端點** | 預設 OpenAI Endpoints | `localhost:8000/v1` | 明確指定 vLLM 兼容的 API 介面，支援 OpenAI Client SDK 呼叫。 |
| **依賴庫** | 僅基礎科學計算庫 | 新增 `openai`, `time` | 引入官方 SDK 以獲得更穩定的連線控制；引入時間模組以監控效能。 |

## 3. 穩定性與容錯機制 (Stability & Robustness)

針對長時間運行的評測任務，優化版本引入了多項防禦性程式設計 (Defensive Programming) 措施。

### 3.1 異常處理與重試策略 (Retry Backoff)
*   **原始設計**: 發生例外 (Exception) 時立即重試，容易在伺服器過載或短暫連線問題時造成連續失敗 (Thundering Herd Problem)。
*   **優化設計**: 引入 **指數退避 (Exponential Backoff)** 概念的簡化版，在失敗後強制 `time.sleep(2)`。這給予伺服器緩衝時間，顯著提高了批次處理的成功率。

### 3.2 資料完整性檢查 (Data Integrity)
*   **Key Error 防護**: 在存取 `all_questions` 字典前，新增 `if q_name in all_questions` 檢查，防止因索引不一致導致的程式崩潰 (Crash)。
*   **空值檢查**: 在解析模型發生錯誤或回傳空值時，透過 `if q in parsed_predicted_answers` 進行驗證，確保不會寫入無效資料導致評分階段錯誤。

## 4. 可觀察性與報告輸出 (Observability & Reporting)

### 4.1 執行效能監控
*   **新增功能**: 實作了完整的實驗計時器 (`experiment_start_time` 至 `experiment_end_time`)。
*   **效益**: 在實驗結束後自動計算並格式化顯示總耗時 (Total Duration)，有助於評估不同硬體或量化設定下的推論效能 (Inference Latency)。

### 4.2 中間狀態保存 (Checkpointing)
*   **策略調整**: 存檔頻率由「每 5 個批次」提升為「**每一批次 (Per Batch)**」。
*   **效益**: 最小化因意外中斷 (如 OOM 或斷電) 造成的進度損失，確保長時間運算的成果得以保存。

### 4.3 報告格式優化
*   **JSON 序列化**: 輸出檔案時加入 `indent=4` 參數，將單行 JSON 轉為可讀性高的排版格式，便於人工查閱與 Git 版控差異比較。
*   **終端輸出**: 優化了 "Final Report" 的呈現，清晰列出總題數、類別準確率表格與最終平均分數，提供更專業的實驗結案數據。

## 5. 開發體驗 (Developer Experience)

新增 `TEST_LIMIT` 參數 (預設 10 題)，允許開發者在不執行完整測試 (數千題) 的情況下，快速驗證 Pipeline 的正確性與模型連通性，大幅縮短開發迭代週期 (Iteration Cycle)。

---
*報告生成日期: 2026-01-12*
*專案: Tele-LLM Eval*
