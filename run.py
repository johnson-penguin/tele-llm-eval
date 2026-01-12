from evaluation_tools import *
import os 
import json
import numpy as np
import pandas as pd
import openai # Ensure openai library is imported to set global variables
import time
import datetime
from copy import deepcopy

# ================= Configuration =================

# 1. Set local model connection information
# vLLM typically defaults to port 8000
os.environ["OPENAI_API_KEY"] = "EMPTY" 
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"
# Compatibility with older openai packages
openai.api_key = "EMPTY"
openai.base_url = "http://localhost:8000/v1"
openai.api_base = "http://localhost:8000/v1"

# 2. Set model name (must match vLLM's --served-model-name)
model = "log-copilot" 

# 3. Test limit (set to 120 questions)
TEST_LIMIT = 120

# ===========================================================

questions_path = "TeleQnA.txt"
save_path = os.path.join(model + "_answers.txt")

n_questions = 40   # Batch size
max_attempts = 5  # Max retries

print(f"Evaluating model: {model} on Local Server")
print(f"Target Server: {os.environ['OPENAI_BASE_URL']}")

# --- New feature: Start timing ---
experiment_start_time = time.time()
print(f"Experiment started at: {time.ctime(experiment_start_time)}")
# ----------------------------------

# Load questions
with open(questions_path, encoding="utf-8") as f:
    loaded_json = f.read()
all_questions = json.loads(loaded_json)

shuffled_idx = np.arange(len(all_questions))

# Resume logic for interrupted evaluations
if os.path.exists(save_path):
    with open(save_path) as f:
        loaded_json = f.read()
    results = json.loads(loaded_json)
    
    start = len(results)
    categories = [ques['category'] for ques in results.values()]
    correct = [ques['correct'] for ques in results.values()]
    print(f"Resuming from previous results. Already answered: {start}")
else:
    results = {}
    start = 0
    categories = []
    correct = []
    print("Starting new evaluation.")

# --- Key modification: Set end point for limited testing ---
# If (start position + TEST_LIMIT) is less than total questions, test up to that point; otherwise test all remaining questions
target_end = start + TEST_LIMIT
end = np.minimum(target_end, len(all_questions))

print(f"Test range: Question {start} to {end} (Total {end - start} questions)")

k = 0 # Counter for batches

# Main loop
for start_id in range(start, end, n_questions):
    attempts = 0
    # Calculate the end index for this batch
    end_id = np.minimum(start_id + n_questions, end)
    
    # Ensure only questions within the range are selected
    # Note: If shuffle_idx is just arange, questions are selected sequentially
    q_names = ["question {}".format(shuffled_idx[idx]) for idx in range(start_id, end_id)]
    
    selected_questions = {}
    for q_name in q_names:
        # Ensure key exists to prevent index errors
        if q_name in all_questions:
            selected_questions[q_name] = all_questions[q_name]
    
    if not selected_questions:
        print("No questions selected in this batch, finishing.")
        break

    print(f"Processing batch: {q_names[0]} to {q_names[-1]}...")

    while attempts < max_attempts:
        try:
            # Call evaluation tool (this will hit the localhost API)
            accepted_questions, parsed_predicted_answers = check_questions_with_val_output(selected_questions, model)
            
            for q in selected_questions:  
                # Ensure the returned result contains this question
                if q in parsed_predicted_answers:
                    results[q] = deepcopy(selected_questions[q])
                    results[q]['tested answer'] = parsed_predicted_answers[q]['answer']
                    results[q]['correct'] = q in accepted_questions
                    
                    correct += [results[q]['correct']]
                    categories += [selected_questions[q]['category']]
                else:
                    print(f"Warning: Model did not return answer for {q}")
        
            print(f"Batch success. Current accuracy: {np.mean(correct):.2%}")
            break
            
        except Exception as e:
            attempts += 1
            print(f"Attempt {attempts} failed. Error: {e}")
            import time
            time.sleep(2) # Wait a bit after failure
            print("Retrying...")
        
    else:
        print(f"Failed after {max_attempts} attempts for batch starting at {start_id}.")

    k += 1
    # Save after each batch completion, or every 5 batches
    # For testing convenience, save after every batch
    if True: 
        with open(save_path, 'w') as f:
            res_str = json.dumps(results, indent=4) # indent makes json more readable
            f.write(res_str)

        if len(categories) > 0:
            res = pd.DataFrame.from_dict({
                'categories': categories,
                'correct': correct
            })

            summary = res.groupby('categories').mean(numeric_only=True)
            summary['counts'] = res.groupby('categories').count()['correct'].values
            
            print("\n--- Interim Summary ---")
            print(summary)
            print("-----------------------\n")

# Final save and report
with open(save_path, 'w') as f:
    res_str = json.dumps(results, indent=4)
    f.write(res_str)
    
# --- New feature: Calculate and display total time ---
experiment_end_time = time.time()
total_seconds = experiment_end_time - experiment_start_time
formatted_time = str(datetime.timedelta(seconds=int(total_seconds))) # Format as HH:MM:SS
# ------------------------------------------------------
if len(categories) > 0:
    res = pd.DataFrame.from_dict({
        'categories': categories,
        'correct': correct
    })

    summary = res.groupby('categories').mean(numeric_only=True)
    summary['counts'] = res.groupby('categories').count()['correct'].values

    print("\n========== FINAL REPORT ==========")
    print(f"Total number of questions answered: {len(categories)}")
    print(summary)
    print("\nTime", total_seconds)
    print("\nFinal Accuracy: {:.2%}".format(np.mean([q['correct'] for q in results.values()])))
    print("==================================")
else:
    print("No results generated.")

