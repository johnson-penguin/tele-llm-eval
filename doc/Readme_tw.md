# TeleQnA 評測工具 - 本地模型版本

本專案用於評估本地部署的大型語言模型 (LLM) 在 TeleQnA 電信領域基準測試上的表現。程式碼已針對推理模型 (如 QwQ-32b) 進行優化，支援 Chain-of-Thought 評測。

## 專案特色

- 支援本地 vLLM Server (或其他 OpenAI-compatible API)
- 針對推理模型優化的 Prompt 設計 (支援 CoT)
- 斷點續傳功能，避免長時間運行中斷損失
- 自動計時與詳細報告輸出
- 保留模型完整推理過程供分析

## 環境需求

### Python 套件
```bash
pip install openai pandas numpy
```

### TeleQnA 資料集
下載 TeleQnA 資料集並將 `TeleQnA.txt` 放置於專案根目錄：
```bash
git clone https://github.com/netop-team/TeleQnA.git
# 從下載的資料夾中取得 TeleQnA.txt
```

## 使用方法

### 1. 啟動本地模型服務
使用 vLLM 啟動模型 API Server：
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/model \
    --served-model-name log-copilot \
    --port 8000 \
    --trust-remote-code
```

### 2. 配置評測參數
編輯 `run.py` 的配置區域 (第 10-19 行)：

```python
# API 伺服器位址
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"

# 模型名稱 (需與 vLLM 的 --served-model-name 一致)
model = "log-copilot"

# 測試題數限制 (設為 None 或大數字則測試全部)
TEST_LIMIT = 10
```

### 3. 執行評測
```bash
python run.py
```

## 核心功能說明

### evaluation_tools.py
負責與模型互動並解析答案。

**主要函數**:
- `format_single_prompt(q_data)`: 生成 Chain-of-Thought Prompt
- `check_questions_with_val_output(questions_dict, model)`: 評測函數

**設計特點**:
- 採用「逐題詢問」而非批次，確保每題獲得完整推理空間
- 使用 Regex 提取答案，容許模型輸出格式有細微差異
- 僅比對選項 ID，不要求文字完全一致
- 保留完整推理過程於 `full_reasoning` 欄位

### run.py
主程式，負責讀取資料、呼叫評測函數、統計結果。

**關鍵參數**:
- `n_questions = 5`: 每批次處理 5 題
- `max_attempts = 5`: 失敗重試次數
- `TEST_LIMIT = 10`: 限制測試題數 (用於快速驗證)

**特色功能**:
- 斷點續傳：程式中斷後可從上次進度繼續
- 即時存檔：每批次完成後立即寫入硬碟
- 計時功能：自動統計總執行時間
- 詳細報告：顯示各類別準確率與總體表現

## 輸出說明

### 執行過程輸出
```
Evaluating model: log-copilot on Local Server
Target Server: http://localhost:8000/v1
Experiment started at: Sun Jan 12 17:00:00 2026
Starting new evaluation.
Test range: Question 0 to 10 (Total 10 questions)
Processing batch: question 0 to question 4...
Batch success. Current accuracy: 80.00%
...
```

### 結果檔案
產生 `{model}_answers.txt` (如 `log-copilot_answers.txt`)，內容為 JSON 格式：
```json
{
    "question 1": {
        "question": "...",
        "option 1": "...",
        "answer": "option 2",
        "tested answer": "option 2",
        "correct": true,
        "category": "3gpp_standards"
    },
    ...
}
```

## Prompt 設計說明

本專案針對推理模型設計了特殊的 Prompt 格式：
```
You are a telecommunications expert. Please answer the following multiple-choice question.

Question: {question_text}

Option 1: ...
Option 2: ...
...

Please think step-by-step to ensure accuracy. 
At the very end of your response, strictly output the answer in this format: "Answer: Option X"
```

這種設計的優點：
- 激發模型的推理能力 (Chain-of-Thought)
- 不強制輸出 JSON，避免格式錯誤導致解析失敗
- 允許模型充分解釋思考過程

## 引用
若使用 TeleQnA 基準測試，請引用：
```bibtex
@misc{maatouk2023teleqna,
      title={TeleQnA: A Benchmark Dataset to Assess Large Language Models Telecommunications Knowledge}, 
      author={Ali Maatouk and Fadhel Ayed and Nicola Piovesan and Antonio De Domenico and Merouane Debbah and Zhi-Quan Luo},
      year={2023},
      eprint={2310.15051},
      archivePrefix={arXiv},
      primaryClass={cs.IT}
}
```
