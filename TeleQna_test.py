import json
import requests
import time
import re
import os

# --- Configuration ---
API_URL = "http://localhost:8000/v1/chat/completions"
FILE_PATH = "TeleQnA.txt"
MODEL_NAME = "log-copilot"
DETAIL_LOG_PATH = "detailed_results.jsonl"

def run_evaluation():
    if not os.path.exists(FILE_PATH):
        print(f"Error: File {FILE_PATH} not found.")
        return

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = list(data.items())
    total_q = len(questions)
    correct_count = 0
    start_time = time.time()
    
    print(f"Starting evaluation. Total: {total_q}")
    print(f"Detailed logs will be saved to: {DETAIL_LOG_PATH}")
    print("-" * 60)

    with open(DETAIL_LOG_PATH, "a", encoding='utf-8') as f_detail:
        for i, (q_id, entry) in enumerate(questions):
            idx = i + 1
            opts = []
            for n in range(1, 6):
                key = f"option {n}"
                if key in entry:
                    opts.append(f"({chr(64+n)}) {entry[key]}")
            options_str = "\n".join(opts)

            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a telecom expert."},
                    {
                        "role": "user", 
                        "content": f"Please answer the following multiple choice question with an explanation.\n\nQuestion: {entry['question']}\n\nOptions:\n{options_str}\n\nPlease provide:\n1. The correct option (A/B/C/D/E)\n2. A brief explanation."
                    }
                ],
                "max_tokens": 150,
                "temperature": 0
            }

            try:
                response = requests.post(API_URL, json=payload, timeout=30)
                model_output = response.json()['choices'][0]['message']['content']
                gold_match = re.search(r'option (\d)', entry['answer'])
                gold_letter = chr(64 + int(gold_match.group(1))) if gold_match else "N/A"
                is_correct = (f"({gold_letter})" in model_output[:30] or 
                              f"Option {gold_letter}" in model_output[:30] or 
                              model_output.strip().startswith(gold_letter))
                if is_correct:
                    correct_count += 1
            except Exception as e:
                model_output = f"ERROR: {str(e)}"
                is_correct = False
                gold_letter = "ERR"

            record = {"id": q_id, "gold": gold_letter, "is_correct": is_correct}
            f_detail.write(json.dumps(record, ensure_ascii=False) + "\n")

            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            current_acc = (correct_count / idx) * 100

            if idx % 500 == 0 or idx == total_q:
                log_filename = f"evaluation_progress_{idx}.log"
                with open(log_filename, "w", encoding='utf-8') as f_sum:
                    f_sum.write(f"Processed: {idx}\nACC: {current_acc:.2f}%\nElapsed: {elapsed/60:.2f} min")
                print(f"\n[Snapshot Saved]: {log_filename}")

            print(f"Q: {idx}/{total_q} | ACC: {current_acc:.2f}% | ETA: {int((avg_time*(total_q-idx))//60)}m", end='\r')

    print(f"\n\nEvaluation Complete!")

if __name__ == "__main__":
    run_evaluation()
