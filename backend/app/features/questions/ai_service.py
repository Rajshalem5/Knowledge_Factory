"""AI question generation using the Qwen3-coder model."""

import json
import re
import uuid
import httpx
import logging
from app.config import settings
from app.features.questions.schemas import Question, TestCase

logger = logging.getLogger(__name__)

# Ask AI ONLY for problem metadata + test cases — we generate boilerplate ourselves
SYSTEM_PROMPT = """\
You are a competitive programming question generator.
Output ONLY a single valid JSON object. No markdown, no code fences, no explanation.

The JSON must have EXACTLY these keys:
{
  "title": "Short problem title",
  "description": "Full problem statement including input format, output format, and constraints",
  "difficulty": "easy",
  "input_format": "Describe each line of stdin. Example: Line 1: integer n. Line 2: n space-separated integers.",
  "output_format": "Describe stdout. Example: Single integer: the sum.",
  "public_test_cases": [
    {"input": "5\\n1 2 3 4 5", "expected_output": "15"}
  ],
  "private_test_cases": [
    {"input": "3\\n10 20 30", "expected_output": "60"}
  ]
}

RULES:
1. input is EXACT stdin — lines separated by \\n.
2. expected_output is EXACT stdout — no trailing spaces or newlines.
3. difficulty must be exactly: easy, medium, or hard.
4. Do NOT include boilerplate — it will be generated separately.
5. Output ONLY the JSON object."""


# Boilerplate templates — we build these ourselves based on input_format
PYTHON_TEMPLATE = """import sys
input = sys.stdin.readline

def solve():
    # Read input here
    n = int(input())
    arr = list(map(int, input().split()))
    
    # Write your solution here
    
    print(0)  # Replace with your answer

solve()
"""

JAVA_TEMPLATE = """import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int n = Integer.parseInt(br.readLine().trim());
        StringTokenizer st = new StringTokenizer(br.readLine());
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) {
            arr[i] = Integer.parseInt(st.nextToken());
        }
        
        // Write your solution here
        
        System.out.println(0); // Replace with your answer
    }
}
"""

CPP_TEMPLATE = """#include <iostream>
#include <vector>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int n;
    cin >> n;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) cin >> arr[i];
    
    // Write your solution here
    
    cout << 0 << endl; // Replace with your answer
    return 0;
}
"""


def build_boilerplate(input_format: str, sample_input: str = "") -> dict[str, str]:
    """
    Detect input shape from the actual sample input and build correct boilerplate.
    Never trust the AI's input_format description — use the real test case.
    """
    lines = [l for l in sample_input.strip().split("\n") if l.strip()]
    num_lines = len(lines)

    # Detect: single integer on one line
    if num_lines == 1:
        try:
            int(lines[0].strip())
            return {
                "python": "n = int(input())\n\n# Write your solution here\n\nprint(0)  # Replace with your answer\n",
                "java": (
                    "import java.util.*;\npublic class Main {\n"
                    "    public static void main(String[] args) {\n"
                    "        Scanner sc = new Scanner(System.in);\n"
                    "        int n = sc.nextInt();\n"
                    "        // Write your solution here\n"
                    "        System.out.println(0);\n"
                    "    }\n}"
                ),
                "cpp": (
                    "#include<iostream>\nusing namespace std;\nint main(){\n"
                    "    int n; cin>>n;\n"
                    "    // Write your solution here\n"
                    "    cout<<0<<endl;\n"
                    "    return 0;\n}"
                ),
            }
        except ValueError:
            # Single line string input
            return {
                "python": "s = input().strip()\n\n# Write your solution here\n\nprint(0)  # Replace with your answer\n",
                "java": (
                    "import java.util.*;\npublic class Main {\n"
                    "    public static void main(String[] args) {\n"
                    "        Scanner sc = new Scanner(System.in);\n"
                    "        String s = sc.nextLine().trim();\n"
                    "        // Write your solution here\n"
                    "        System.out.println(0);\n"
                    "    }\n}"
                ),
                "cpp": (
                    "#include<iostream>\n#include<string>\nusing namespace std;\nint main(){\n"
                    "    string s; getline(cin,s);\n"
                    "    // Write your solution here\n"
                    "    cout<<0<<endl;\n"
                    "    return 0;\n}"
                ),
            }

    # Detect: line 1 = n, line 2 = n space-separated integers
    if num_lines == 2:
        try:
            n = int(lines[0].strip())
            arr = list(map(int, lines[1].strip().split()))
            if len(arr) == n:
                return {
                    "python": (
                        "import sys\ninput = sys.stdin.readline\n\n"
                        "n = int(input())\n"
                        "arr = list(map(int, input().split()))\n\n"
                        "# Write your solution here\n\n"
                        "print(0)  # Replace with your answer\n"
                    ),
                    "java": (
                        "import java.util.*;\nimport java.io.*;\npublic class Main {\n"
                        "    public static void main(String[] args) throws IOException {\n"
                        "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n"
                        "        int n = Integer.parseInt(br.readLine().trim());\n"
                        "        StringTokenizer st = new StringTokenizer(br.readLine());\n"
                        "        int[] arr = new int[n];\n"
                        "        for(int i=0;i<n;i++) arr[i]=Integer.parseInt(st.nextToken());\n"
                        "        // Write your solution here\n"
                        "        System.out.println(0);\n"
                        "    }\n}"
                    ),
                    "cpp": (
                        "#include<iostream>\n#include<vector>\nusing namespace std;\nint main(){\n"
                        "    int n; cin>>n;\n"
                        "    vector<int> arr(n);\n"
                        "    for(int i=0;i<n;i++) cin>>arr[i];\n"
                        "    // Write your solution here\n"
                        "    cout<<0<<endl;\n"
                        "    return 0;\n}"
                    ),
                }
        except (ValueError, IndexError):
            pass

    # Fallback: read all input as tokens — works for any shape
    return {
        "python": (
            "import sys\n\n"
            "data = sys.stdin.read().split()\nidx = 0\n\n"
            "# Example: n = int(data[idx]); idx += 1\n"
            "# Write your solution here\n\n"
            "print(0)  # Replace with your answer\n"
        ),
        "java": (
            "import java.util.*;\npublic class Main {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n"
            "        // Read input with sc.nextInt(), sc.next(), etc.\n"
            "        // Write your solution here\n"
            "        System.out.println(0);\n"
            "    }\n}"
        ),
        "cpp": (
            "#include<iostream>\nusing namespace std;\nint main(){\n"
            "    // Read input with cin\n"
            "    // Write your solution here\n"
            "    cout<<0<<endl;\n"
            "    return 0;\n}"
        ),
    }


async def generate_question(
    topic: str = "arrays",
    difficulty: str = "medium",
    num_public: int = 2,
    num_private: int = 4,
) -> Question:
    import secrets
    salt = secrets.token_hex(4)
    user_prompt = (
        f"Generate a unique and creative {difficulty} coding problem about: {topic}. "
        f"Ensure it is different from common standard problems. [Seed: {salt}] "
        f"Include {num_public} public test cases and {num_private} private test cases. "
        f"stdin/stdout only. Output ONLY JSON."
    )

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            settings.AI_API_URL,
            headers={
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # Extract first JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in AI response: {raw[:300]}")

    parsed = json.loads(match.group(0))

    for key in ("title", "description", "public_test_cases", "private_test_cases"):
        if key not in parsed:
            raise ValueError(f"AI response missing key: {key}")

    # Normalise test cases
    def make_cases(lst: list, is_public: bool) -> list[TestCase]:
        out = []
        for tc in lst:
            inp = str(tc.get("input", "")).rstrip("\n")
            expected = str(tc.get("expected_output", "")).strip()
            if inp and expected:
                out.append(TestCase(input=inp, expected_output=expected, is_public=is_public))
        return out

    public_cases  = make_cases(parsed["public_test_cases"],  True)
    private_cases = make_cases(parsed["private_test_cases"], False)

    if not public_cases:
        raise ValueError("AI returned no valid public test cases")

    # Build boilerplate from the actual first test case input — not AI's description
    sample_input = public_cases[0].input if public_cases else ""
    input_format = parsed.get("input_format", "")
    boilerplate = build_boilerplate(input_format, sample_input)

    return Question(
        id=f"q_{uuid.uuid4().hex[:8]}",
        title=parsed["title"],
        description=parsed["description"],
        difficulty=parsed.get("difficulty", difficulty).lower(),
        boilerplate=boilerplate,
        public_test_cases=public_cases,
        private_test_cases=private_cases,
    )


MCQ_SYSTEM_PROMPT = """\
You are an expert technical interviewer.
Generate multiple-choice questions (MCQs) for a software engineering role.
Output ONLY a single valid JSON object. No markdown, no code fences, no explanation.

The JSON must have EXACTLY this key:
{
  "questions": [
    {
      "id": "unique_string_id",
      "question": "The question text. Can include code snippets.",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Why this answer is correct",
      "difficulty": "easy|medium|hard",
      "topic": "OS"
    }
  ]
}

RULES:
1. correct_answer must be the EXACT string match of one of the options.
2. Provide exactly 4 options per question.
3. difficulty must be exactly: easy, medium, or hard.
4. topic must be the specific subject being tested.
5. Output ONLY the JSON object."""


async def generate_mcq_questions(
    topic: str = "CS Fundamentals",
    difficulty: str = "medium",
    count: int = 5,
) -> list[dict]:
    import secrets
    salt = secrets.token_hex(4)
    user_prompt = (
        f"Generate {count} unique and creative {difficulty} level MCQ questions about: {topic}. "
        f"Ensure variety and avoid common, overused questions. [Seed: {salt}] "
        f"Output ONLY JSON."
    )

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": MCQ_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            resp = await client.post(
                settings.AI_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return []

    raw = resp.json()["choices"][0]["message"]["content"].strip()
    
    # Clean and parse JSON
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        logger.error(f"No JSON in AI response: {raw[:300]}")
        return []

    try:
        parsed = json.loads(match.group(0))
        questions = parsed.get("questions", [])
        for q in questions:
            if not q.get("id"):
                q["id"] = f"mcq_{uuid.uuid4().hex[:8]}"
            # Ensure correct_answer is an index if the user wants to keep the evaluation simple,
            # but user said "correct_answer": "..." in their format example.
            # I will store both for safety or just follow the example.
            # Let's check which evaluation is easier. String match is fine.
        return questions
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        return []
