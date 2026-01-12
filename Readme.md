# TeleQnA Evaluation Tool - Local Model Version

This project evaluates locally deployed Large Language Models (LLMs) on the TeleQnA telecommunications benchmark. The code is optimized for reasoning models (such as QwQ-32B) with Chain-of-Thought (CoT) evaluation support.

## Features

- Support for local vLLM server (or any OpenAI-compatible API)
- Optimized prompt design for reasoning models with CoT support
- Checkpoint recovery to prevent progress loss during long evaluation runs
- Automatic timing and detailed statistical reporting
- Full reasoning trace preservation for in-depth analysis
- Parallel processing support for faster evaluation

## Requirements

### Python Packages
```bash
pip install -r requirements.txt
```

### TeleQnA Dataset
Download the TeleQnA dataset and place `TeleQnA.txt` in the project root directory:
```bash
git clone https://github.com/netop-team/TeleQnA.git
# Extract TeleQnA.txt from the downloaded repository
```

## Usage

### 1. Start Local Model Service
Launch the model API server using vLLM:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/your/model \
    --served-model-name log-copilot \
    --port 8000 \
    --trust-remote-code
```

### 2. Configure Evaluation Parameters
Edit the configuration section in `run.py` (lines 11-26):

```python
# API server address
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"

# Model name (must match vLLM's --served-model-name)
model = "log-copilot"

# Test limit (adjust based on your hardware capabilities)
# Set to a larger number or remove limit for full dataset evaluation
TEST_LIMIT = 120
```

### 3. Run Evaluation
```bash
python run.py
```

The evaluation will display real-time progress and save results after each batch to prevent data loss.

## Core Components

### evaluation_tools.py
Handles model interaction, prompt formatting, and answer parsing.

**Main Functions**:
- `format_single_prompt(q_data)`: Generates optimized Chain-of-Thought prompts for telecommunications questions
- `process_single_question(q_id, q_data, model)`: Processes individual questions with error handling
- `check_questions_with_val_output(questions_dict, model)`: Main evaluation function with parallel processing support

**Design Features**:
- ThreadPoolExecutor-based parallel processing for improved throughput
- Regex-based answer extraction to handle format variations gracefully
- Option ID comparison only—no strict text matching required
- Full reasoning trace preserved in `full_reasoning` field for analysis
- Configurable worker count (adjust `MAX_WORKERS` based on available VRAM)

### run.py
Main evaluation pipeline that orchestrates data loading, model evaluation, and statistics computation.

**Key Parameters** (adjust based on hardware capabilities):
- `n_questions = 40`: Batch size for processing questions
- `max_attempts = 5`: Maximum retry attempts per batch on failure
- `TEST_LIMIT = 120`: Question limit for quick validation runs
- `MAX_WORKERS = 40`: Parallel worker threads (in `evaluation_tools.py`)

**Key Features**:
- **Checkpoint recovery**: Automatically resumes from previous progress after interruption
- **Incremental saving**: Results written to disk after each batch to prevent data loss
- **Timing statistics**: Automatic tracking and reporting of total runtime
- **Detailed reporting**: Category-wise accuracy breakdown and overall performance metrics

## Output Description

### Runtime Output
```
Evaluating model: log-copilot on Local Server
Target Server: http://localhost:8000/v1
Experiment started at: Sun Jan 12 17:00:00 2026
Starting new evaluation.
Test range: Question 0 to 120 (Total 120 questions)
Processing batch: question 0 to question 39...
Batch success. Current accuracy: 85.00%

--- Interim Summary ---
                correct  counts
categories                      
Lexicon        0.876543      81
Technical      0.823529      34
...
-----------------------

========== FINAL REPORT ==========
Total number of questions answered: 120
                correct  counts
categories                      
Lexicon        0.869565     115
Technical      0.800000       5

Time: 1234.56
Final Accuracy: 86.67%
==================================
```

### Result Files
Results are saved in the current directory as `{model}_answers.txt` (e.g., `log-copilot_answers.txt`) in JSON format:

For organized storage, consider moving results to `tele-llm-eval\Result\model_answer\`

```json
{
    "question 1": {
        "question": "What does VPN stand for?",
        "option 1": "Voice Packet Network",
        "option 2": "Virtual Private Network",
        "option 3": "Visual Presentation Network",
        "option 4": "Voice and Picture Network",
        "option 5": "Video Protocol Network",
        "answer": "option 2: Virtual Private Network",
        "explanation": "VPN stands for Virtual Private Network.",
        "category": "Lexicon",
        "tested answer": "option 2",
        "correct": true
    },
    ...
}
```

## Prompt Design

This project uses a specialized prompt format optimized for reasoning models:

```
You are a telecommunications expert. Please answer the following multiple-choice question.

Question: {question_text}

Option 1: ...
Option 2: ...
...

Please think step-by-step to ensure accuracy. 
At the very end of your response, strictly output the answer in this format: "Answer: Option X", where X is the option number.
```

**Advantages of This Design**:
- **Triggers reasoning capabilities**: Encourages models to use Chain-of-Thought reasoning
- **Format flexibility**: No strict JSON output requirement, avoiding parsing failures
- **Transparent reasoning**: Preserves full explanation for result verification and analysis
- **Robust extraction**: Regex-based parsing handles minor format variations

## Performance Tips

- **Batch size**: Adjust `n_questions` based on your model's context window
- **Parallel workers**: Tune `MAX_WORKERS` based on available GPU memory (5-10 for safety, 40+ for high-end GPUs)
- **Test limit**: Use `TEST_LIMIT` for quick validation before running full evaluation
- **Checkpointing**: The tool automatically saves progress—feel free to interrupt and resume

## Citation

If you use the TeleQnA benchmark in your research, please cite:

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
