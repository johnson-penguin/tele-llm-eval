# TeleQnA Evaluation Tool - Local Model Version

This project evaluates locally deployed Large Language Models (LLMs) on the TeleQnA telecommunications benchmark. The code is optimized for reasoning models (such as QwQ-32b) with Chain-of-Thought evaluation support.

## Features

- Support for local vLLM Server (or any OpenAI-compatible API)
- Optimized prompt design for reasoning models (CoT support)
- Checkpoint recovery to prevent progress loss during long runs
- Automatic timing and detailed reporting
- Full reasoning trace preservation for analysis

## Requirements

### Python Packages
```bash
pip install openai pandas numpy
```

### TeleQnA Dataset
Download the TeleQnA dataset and place `TeleQnA.txt` in the project root:
```bash
git clone https://github.com/netop-team/TeleQnA.git
# Extract TeleQnA.txt from the downloaded directory
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
Edit the configuration section in `run.py` (lines 10-19):

```python
# API server address
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"

# Model name (must match vLLM's --served-model-name)
model = "log-copilot"

# Test limit (set to None or large number for full evaluation)
TEST_LIMIT = 10
```

### 3. Run Evaluation
```bash
python run.py
```

## Core Components

### evaluation_tools.py
Handles model interaction and answer parsing.

**Main Functions**:
- `format_single_prompt(q_data)`: Generates Chain-of-Thought prompts
- `check_questions_with_val_output(questions_dict, model)`: Evaluation function

**Design Features**:
- Single-question iteration instead of batching for complete reasoning space
- Regex-based answer extraction to tolerate format variations
- Option ID comparison only, no strict text matching required
- Full reasoning trace preserved in `full_reasoning` field

### run.py
Main program that loads data, calls evaluation functions, and computes statistics.

**Key Parameters**:
- `n_questions = 5`: Batch size for processing
- `max_attempts = 5`: Maximum retry attempts
- `TEST_LIMIT = 10`: Question limit for quick validation

**Key Features**:
- Checkpoint recovery: Resume from previous progress after interruption
- Immediate save: Results written to disk after each batch
- Timing: Automatic total runtime statistics
- Detailed reports: Category-wise accuracy and overall performance

## Output Description

### Runtime Output
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

### Result Files
Generates `{model}_answers.txt` (e.g., `log-copilot_answers.txt`) in JSON format:
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

## Prompt Design

This project uses a specialized prompt format for reasoning models:
```
You are a telecommunications expert. Please answer the following multiple-choice question.

Question: {question_text}

Option 1: ...
Option 2: ...
...

Please think step-by-step to ensure accuracy. 
At the very end of your response, strictly output the answer in this format: "Answer: Option X"
```

Advantages of this design:
- Triggers the model's reasoning capabilities (Chain-of-Thought)
- No strict JSON output requirement, avoiding parsing failures
- Allows full explanation of the reasoning process

## Citation
If you use the TeleQnA benchmark, please cite:
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
