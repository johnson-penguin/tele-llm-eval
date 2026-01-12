import os
import re
import concurrent.futures
from openai import OpenAI

# 1. Set up Client
client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
    api_key=os.environ.get("OPENAI_API_KEY", "EMPTY")
)

def format_single_prompt(q_data):
    """
    Optimized prompt format for QwQ/log-copilot.
    """
    question_text = q_data.get('question', '')
    
    options = {}
    for key, value in q_data.items():
        if key.startswith('option'):
            try:
                opt_id = int(key.split(' ')[1])
                options[opt_id] = value
            except:
                continue
    
    options_str = ""
    for opt_id in sorted(options.keys()):
        options_str += f"Option {opt_id}: {options[opt_id]}\n"
    
    prompt = f"""You are a telecommunications expert. Please answer the following multiple-choice question.

Question: {question_text}

{options_str}

Please think step-by-step to ensure accuracy. 
At the very end of your response, strictly output the answer in this format: "Answer: Option X", where X is the option number.
"""
    return prompt

def process_single_question(q_id, q_data, model):
    """
    Processing function for a single question (used for parallel execution)
    """
    try:
        correct_answer_str = q_data.get('answer', '') 
        prompt = format_single_prompt(q_data)
        
        # Call API
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2048,
            extra_body={"top_k": 50}
        )
        
        raw_output = response.choices[0].message.content
        
        # Parse answer
        match = re.search(r"Answer:\s*Option\s*(\d+)", raw_output, re.IGNORECASE)
        if not match:
            matches = re.findall(r"Option\s*(\d+)", raw_output, re.IGNORECASE)
            pred_id = matches[-1] if matches else None
        else:
            pred_id = match.group(1)
        
        final_answer_str = f"option {pred_id}" if pred_id else "No Answer Found"
        
        # Determine correctness
        is_correct = False
        if pred_id:
            correct_match = re.match(r"option\s*(\d+)", correct_answer_str, re.IGNORECASE)
            correct_id = correct_match.group(1) if correct_match else None
            if correct_id and pred_id == correct_id:
                is_correct = True
                
        return q_id, {
            "question": q_data.get('question', ''),
            "answer": final_answer_str, 
            "full_reasoning": raw_output
        }, is_correct

    except Exception as e:
        print(f"Error processing {q_id}: {e}")
        return q_id, {
            "question": q_data.get('question', ''),
            "answer": f"Error: {str(e)}"
        }, False

def check_questions_with_val_output(questions_dict, model):
    """
    Modified evaluation function: Uses ThreadPoolExecutor for parallel processing
    """
    parsed_predicted_answers = {}
    accepted_questions = []
    
    # Set parallel count (adjust based on VRAM size, typically 5-10 is safe)
    MAX_WORKERS = 40
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_qid = {
            executor.submit(process_single_question, q_id, q_data, model): q_id 
            for q_id, q_data in questions_dict.items()
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_qid):
            q_id = future_to_qid[future]
            try:
                q_id_res, result_data, is_correct = future.result()
                
                parsed_predicted_answers[q_id] = result_data
                if is_correct:
                    accepted_questions.append(q_id)
                    
            except Exception as exc:
                print(f'{q_id} generated an exception: {exc}')

    return accepted_questions, parsed_predicted_answers