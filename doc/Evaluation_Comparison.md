# evaluation_tools.py 修改差異分析

此文件說明 `evaluation_tools.py` 的修改內容與原因，主要針對本地端的推理模型 (如 QwQ) 進行適配。

## 1. API 連線方式 (Client Setup)
*   **修改內容**: 將原本的全域 `openai.api_key` 設定，改為建立一個 `OpenAI` Client 實例，並讀取環境變數。
*   **修改原因**: 為了能夠連線到本地架設的 vLLM Server。

```bash=
# 原始版本
openai.api_key = " " ## Insert OpenAI's API key

# 修改版本
client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
    api_key=os.environ.get("OPENAI_API_KEY", "EMPTY")
)
```

## 2. 提示詞策略 (Prompting)
*   **修改內容**: 棄用強制 JSON 輸出的 System Prompt，改用 CoT (Chain-of-Thought) 的方式。
*   **修改原因**: 推理模型 (Reasoning Models) 不適合強制輸出 JSON，讓其一步步思考 (Step-by-Step) 準確率較高。

```bash=
# 原始版本
syst_prompt = """... The questions will be in a JSON format ..."""

# 修改版本
prompt = f"""...
Please think step-by-step to ensure accuracy. 
At the very end of your response, strictly output the answer in this format: "Answer: Option X"
"""
```

## 3. 答案解析方式 (Parsing)
*   **修改內容**: 移除 `ast.literal_eval`，改用 Regex 提取答案。
*   **修改原因**: 模型現在輸出的是自然語言而非 JSON，無法使用 Python 語法解析器。

```bash=
# 原始版本
parsed_predicted_answers = ast.literal_eval(predicted_answers_str)

# 修改版本
match = re.search(r"Answer:\s*Option\s*(\d+)", raw_output, re.IGNORECASE)
pred_id = match.group(1) if match else None
```

## 4. 批次處理邏輯 (Batching)
*   **修改內容**: 改為函數內部「單題迴圈」處理。
*   **修改原因**: 避免因單題漏答或格式錯誤導致整批資料無法解析。

```bash=
# 原始版本 (一次傳入所有題目)
generated_output = openai.ChatCompletion.create(..., content=user_prompt)

# 修改版本 (逐題迴圈)
for q_id, q_data in questions_dict.items():
    response = client.chat.completions.create(...)
```

## 5. 對錯判定標準 (Validation)
*   **修改內容**: 從「嚴格文字比對」改為「選項 ID 比對」。
*   **修改原因**: 容許模型生成的答案文字有細微差異 (如標點符號)，只要選項 ID 正確即算得分。

```bash=
# 原始版本 (嚴格比對整個 Dict)
if parsed_predicted_answers[q] == answers_only[q]:

# 修改版本 (僅比對 ID)
if correct_id and pred_id == correct_id:
```
