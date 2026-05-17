"""AI question generation with local fallback."""

import json
import random
import re
import uuid
from typing import Any

import httpx
from app.config import settings
from app.features.questions.schemas import Question, TestCase

# Track recently generated question titles to avoid duplicates
_recent_titles: set = set()
_RECENT_TITLES_MAX = 50

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


# ── Local fallback question pool ───────────────────────────────────

LOCAL_QUESTIONS: dict[str, list[dict[str, Any]]] = {
    "arrays": [
        {
            "title": "Sum of Array Elements",
            "description": "Given an array of N integers, find the sum of all elements.\n\nInput Format:\nLine 1: An integer N (1 ≤ N ≤ 1000)\nLine 2: N space-separated integers\n\nOutput Format:\nPrint a single integer — the sum of all array elements.",
            "difficulty": "easy",
            "public": [({"input": "5\n1 2 3 4 5", "expected": "15"}, {"input": "3\n10 20 30", "expected": "60"})],
            "private": [({"input": "1\n7", "expected": "7"}, {"input": "6\n-1 -2 -3 4 5 6", "expected": "9"}, {"input": "4\n100 200 300 400", "expected": "1000"}, {"input": "10\n1 1 1 1 1 1 1 1 1 1", "expected": "10"})],
        },
        {
            "title": "Find Maximum Element",
            "description": "Given an array of N integers, find the maximum element.\n\nInput Format:\nLine 1: An integer N (1 ≤ N ≤ 1000)\nLine 2: N space-separated integers (-10^6 ≤ Ai ≤ 10^6)\n\nOutput Format:\nPrint a single integer — the maximum element.",
            "difficulty": "easy",
        },
        {
            "title": "Reverse an Array",
            "description": "Given an array of N integers, reverse it and print the result.\n\nInput Format:\nLine 1: An integer N (1 ≤ N ≤ 1000)\nLine 2: N space-separated integers\n\nOutput Format:\nPrint N space-separated integers — the reversed array.",
            "difficulty": "easy",
        },
    ],
    "strings": [
        {
            "title": "Palindrome Check",
            "description": "Given a string S, check if it is a palindrome (reads same forwards and backwards). Ignore case and spaces.\n\nInput Format:\nA single line containing the string S (1 ≤ |S| ≤ 1000)\n\nOutput Format:\nPrint \"YES\" if palindrome, \"NO\" otherwise.",
            "difficulty": "easy",
        },
        {
            "title": "Count Vowels",
            "description": "Given a string S, count the number of vowels (a, e, i, o, u) in it. Case-insensitive.\n\nInput Format:\nA single line containing the string S (1 ≤ |S| ≤ 10000)\n\nOutput Format:\nPrint a single integer — the vowel count.",
            "difficulty": "easy",
        },
    ],
    "sorting": [
        {
            "title": "Bubble Sort Steps",
            "description": "Given an array of N integers, perform one pass of bubble sort and print the array.\n\nInput Format:\nLine 1: An integer N (1 ≤ N ≤ 100)\nLine 2: N space-separated integers\n\nOutput Format:\nPrint the array after one bubble sort pass.",
            "difficulty": "medium",
        },
        {
            "title": "Merge Two Sorted Arrays",
            "description": "Given two sorted arrays, merge them into one sorted array.\n\nInput Format:\nLine 1: N M (sizes of two arrays)\nLine 2: N space-separated integers (sorted)\nLine 3: M space-separated integers (sorted)\n\nOutput Format:\nPrint N+M space-separated integers — the merged sorted array.",
            "difficulty": "medium",
        },
    ],
    "binary search": [
        {
            "title": "Find Element in Sorted Array",
            "description": "Given a sorted array of N integers and a target value, find its index (0-based) using binary search. Return -1 if not found.\n\nInput Format:\nLine 1: N target\nLine 2: N space-separated integers (sorted ascending)\n\nOutput Format:\nPrint the index or -1.",
            "difficulty": "medium",
        },
    ],
    "graphs": [
        {
            "title": "BFS Traversal",
            "description": "Given an undirected graph with N vertices and M edges, perform BFS starting from vertex 0 and print the order of visitation.\n\nInput Format:\nLine 1: N M\nNext M lines: u v (edge between u and v)\n\nOutput Format:\nPrint N space-separated integers — BFS traversal order.",
            "difficulty": "hard",
        },
    ],
    "default": [
        {
            "title": "Two Sum",
            "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nInput Format:\nLine 1: N target\nLine 2: N space-separated integers\n\nOutput Format:\nPrint two space-separated integers — the indices (0-based) of the two numbers.",
            "difficulty": "easy",
            "public": [({"input": "4 9\n2 7 11 15", "expected": "0 1"}, {"input": "3 6\n3 2 4", "expected": "1 2"})],
            "private": [({"input": "4 10\n1 3 5 7", "expected": "1 3"}, {"input": "2 0\n0 4", "expected": "0 0"}, {"input": "5 8\n1 4 6 2 3", "expected": "1 4"}, {"input": "3 100\n10 20 30", "expected": "-1 -1"})],
        },
    ],
}


def build_boilerplate(input_format: str, sample_input: str = "") -> dict[str, str]:
    """Build boilerplate code from sample input."""
    import re

    lines = [l for l in sample_input.strip().split("\n") if l.strip()]
    num_lines = len(lines)

    # Single integer
    if num_lines == 1:
        try:
            int(lines[0].strip())
            return {
                "python": "n = int(input())\n\n# Write your solution here\n\nprint(0)  # Replace with your answer\n",
                "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        // Write your solution here\n        System.out.println(0);\n    }\n}\n",
                "cpp": "#include<iostream>\nusing namespace std;\nint main() {\n    int n; cin >> n;\n    // Write your solution here\n    cout << 0 << endl;\n    return 0;\n}\n",
            }
        except ValueError:
            return {"python": "s = input().strip()\n\n# Write your solution here\n\nprint(0)\n", "java": "", "cpp": ""}

    # n + array of n ints
    if num_lines >= 2:
        try:
            n = int(lines[0].strip())
            list(map(int, lines[1].strip().split()))
            if len(lines[1].strip().split()) == n or num_lines == 2:
                return {
                    "python": "import sys\ninput = sys.stdin.readline\nn = int(input())\narr = list(map(int, input().split()))\n\n# Write your solution here\nprint(0)\n",
                    "java": "import java.util.*;\nimport java.io.*;\npublic class Main {\n    public static void main(String[] args) throws IOException {\n        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        int n = Integer.parseInt(br.readLine().trim());\n        StringTokenizer st = new StringTokenizer(br.readLine());\n        int[] arr = new int[n];\n        for(int i=0;i<n;i++) arr[i]=Integer.parseInt(st.nextToken());\n        System.out.println(0);\n    }\n}\n",
                    "cpp": "#include<iostream>\n#include<vector>\nusing namespace std;\nint main() {\n    int n; cin>>n;\n    vector<int> arr(n);\n    for(int i=0;i<n;i++) cin>>arr[i];\n    cout<<0<<endl;\n    return 0;\n}\n",
                }
        except (ValueError, IndexError):
            pass

    # Fallback
    return {"python": "data = sys.stdin.read().split()\n\n# Write your solution here\nprint(0)\n", "java": "", "cpp": ""}


def _generate_local_question(topic: str, difficulty: str) -> Question:
    """Generate a question locally when AI is unavailable."""
    import random

    pool = LOCAL_QUESTIONS.get(topic.lower(), LOCAL_QUESTIONS.get("default", LOCAL_QUESTIONS["default"]))
    candidates = [q for q in pool if q.get("difficulty", "easy") == difficulty]
    if not candidates:
        candidates = pool
    q_data = random.choice(candidates)

    # Build test cases
    topic_key = topic.lower() if topic.lower() in LOCAL_QUESTIONS else "default"
    pool2 = LOCAL_QUESTIONS[topic_key]
    matching = [q for q in pool2 if q["title"] == q_data["title"]]
    q2 = matching[0] if matching else pool2[0]

    public_cases = []
    private_cases = []

    # Generate test cases from the template data
    raw_public = q2.get("public")
    raw_private = q2.get("private")
    if raw_public is not None:
        for tc_dict in raw_public[0] if isinstance(raw_public[0], dict) else raw_public:
            if isinstance(tc_dict, dict):
                public_cases.append(TestCase(input=str(tc_dict["input"]), expected_output=str(tc_dict["expected"]), is_public=True))
    if raw_private is not None:
        for tc_dict in raw_private[0] if isinstance(raw_private[0], dict) else raw_private:
            if isinstance(tc_dict, dict):
                private_cases.append(TestCase(input=str(tc_dict["input"]), expected_output=str(tc_dict["expected"]), is_public=False))

    # Fallback: generate basic test cases if none defined in template
    if not public_cases:
        r = random.Random(q_data["title"])
        for i in range(2):
            n = r.randint(3, 8)
            arr = [r.randint(1, 20) for _ in range(n)]
            inp = f"{n}\n{' '.join(map(str, arr))}"
            public_cases.append(TestCase(input=inp, expected_output="0", is_public=True))
    if not private_cases:
        r = random.Random(q_data["title"] + "_private")
        for i in range(4):
            n = r.randint(5, 15)
            arr = [r.randint(-10, 50) for _ in range(n)]
            inp = f"{n}\n{' '.join(map(str, arr))}"
            private_cases.append(TestCase(input=inp, expected_output="0", is_public=False))

    boilerplate = {
        "python": "n = int(input())\narr = list(map(int, input().split()))\n\n# Write your solution here\n\nprint(0)  # Replace with your answer\n",
        "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        int[] arr = new int[n];\n        for(int i=0;i<n;i++) arr[i]=sc.nextInt();\n        // Write your solution here\n        System.out.println(0);\n    }\n}\n",
        "cpp": "#include<iostream>\n#include<vector>\nusing namespace std;\nint main() {\n    int n; cin>>n;\n    vector<int> arr(n);\n    for(int i=0;i<n;i++) cin>>arr[i];\n    // Write your solution here\n    cout<<0<<endl;\n    return 0;\n}\n",
    }

    return Question(
        id=f"q_{uuid.uuid4().hex[:8]}",
        title=q_data["title"],
        description=q_data["description"],
        difficulty=q_data.get("difficulty", difficulty).lower(),
        boilerplate=boilerplate,
        public_test_cases=public_cases,
        private_test_cases=private_cases,
    )


async def generate_question(
    topic: str = "arrays",
    difficulty: str = "medium",
    num_public: int = 2,
    num_private: int = 4,
) -> Question:
    """Generate a question — tries AI first, falls back to local on failure."""

    # Skip AI if no API key configured
    use_ai = bool(settings.AI_API_KEY)
    if use_ai and settings.AI_API_KEY.startswith("sk-") and len(settings.AI_API_KEY) < 20:
        use_ai = False

    if not use_ai:
        import logging
        logging.getLogger(__name__).warning("AI_API_KEY not configured. Using local fallback.")
        return _generate_local_question(topic, difficulty)

    # Try AI generation with up to 3 attempts (for dedup + transient failures)
    max_attempts = 3
    for attempt in range(max_attempts):
        seed = random.randint(0, 999999)
        user_prompt = (
            f"Generate a completely UNIQUE {difficulty} coding problem about: {topic}. "
            f"Include exactly {num_public} public test cases and {num_private} private test cases. "
            f"stdin/stdout only. Output ONLY JSON. "
            f"Do NOT reuse titles from Two Sum, Reverse Array, Palindrome Check, FizzBuzz, or any standard problem. "
            f"Think of a fresh scenario. Seed: {seed}"
        )

        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 2000,
            "temperature": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
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

            # Dedup check — retry if title seen recently
            global _recent_titles
            title = parsed["title"]
            if title in _recent_titles:
                raise ValueError(f"Duplicate title generated: {title}")

            _recent_titles.add(title)
            if len(_recent_titles) > _RECENT_TITLES_MAX:
                _recent_titles.clear()

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

            public_cases = make_cases(parsed["public_test_cases"], True)
            private_cases = make_cases(parsed["private_test_cases"], False)

            if not public_cases:
                raise ValueError("AI returned no valid public test cases")

            # Fallback: generate private test cases locally if AI didn't return any
            if not private_cases:
                sr = random.Random(parsed["title"] + "_private")
                for _ in range(num_private):
                    n = sr.randint(5, 15)
                    arr = [sr.randint(-10, 50) for _ in range(n)]
                    inp = f"{n}\n{' '.join(map(str, arr))}"
                    private_cases.append(TestCase(input=inp, expected_output="0", is_public=False))

            # Build boilerplate from the actual first test case input
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

        except Exception as exc:
            import logging
            if attempt < max_attempts - 1:
                logging.getLogger(__name__).warning(
                    "AI generation attempt %d/%d failed (%s). Retrying...",
                    attempt + 1, max_attempts, exc,
                )
                continue
            logging.getLogger(__name__).warning(
                "AI generation failed after %d attempts (%s). Using local fallback.",
                max_attempts, exc,
            )
            return _generate_local_question(topic, difficulty)
