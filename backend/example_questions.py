"""
Example questions with test cases for the assessment system.
This shows the structure for the next phase: Question Generation.
"""

EXAMPLE_QUESTIONS = [
    {
        "id": "q1",
        "title": "Sum of Array",
        "difficulty": "easy",
        "description": """
Given an integer n and an array of n integers, calculate and print the sum of all elements.

**Input Format:**
- First line: integer n (number of elements)
- Second line: n space-separated integers

**Output Format:**
- Single integer: sum of all elements

**Constraints:**
- 1 ≤ n ≤ 10^5
- -10^9 ≤ array[i] ≤ 10^9
""",
        "boilerplate": {
            "python": """n = int(input())
arr = list(map(int, input().split()))
# Write your solution here
""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // Write your solution here
    }
}""",
            "cpp": """#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    // Write your solution here
    return 0;
}"""
        },
        "visible_test_cases": [
            {
                "input": "5\n1 2 3 4 5",
                "expected_output": "15",
                "explanation": "Sum of 1+2+3+4+5 = 15"
            },
            {
                "input": "3\n10 20 30",
                "expected_output": "60",
                "explanation": "Sum of 10+20+30 = 60"
            }
        ],
        "hidden_test_cases": [
            {
                "input": "1\n42",
                "expected_output": "42"
            },
            {
                "input": "6\n-10 20 -30 40 -50 60",
                "expected_output": "30"
            },
            {
                "input": "3\n1000000000 1000000000 1000000000",
                "expected_output": "3000000000"
            },
            {
                "input": "4\n0 0 0 0",
                "expected_output": "0"
            }
        ],
        "solution": {
            "python": """n = int(input())
arr = list(map(int, input().split()))
print(sum(arr))""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        long sum = 0;
        for(int i = 0; i < n; i++) {
            sum += sc.nextLong();
        }
        System.out.println(sum);
    }
}""",
            "cpp": """#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    long long sum = 0, x;
    for(int i = 0; i < n; i++) {
        cin >> x;
        sum += x;
    }
    cout << sum;
    return 0;
}"""
        }
    },
    {
        "id": "q2",
        "title": "Factorial",
        "difficulty": "easy",
        "description": """
Calculate the factorial of a given number n.

Factorial of n (n!) = n × (n-1) × (n-2) × ... × 2 × 1

**Input Format:**
- Single integer n

**Output Format:**
- Single integer: factorial of n

**Constraints:**
- 0 ≤ n ≤ 20
""",
        "boilerplate": {
            "python": """n = int(input())
# Write your solution here
""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        // Write your solution here
    }
}""",
            "cpp": """#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    // Write your solution here
    return 0;
}"""
        },
        "visible_test_cases": [
            {
                "input": "5",
                "expected_output": "120",
                "explanation": "5! = 5 × 4 × 3 × 2 × 1 = 120"
            },
            {
                "input": "0",
                "expected_output": "1",
                "explanation": "0! = 1 (by definition)"
            }
        ],
        "hidden_test_cases": [
            {
                "input": "1",
                "expected_output": "1"
            },
            {
                "input": "10",
                "expected_output": "3628800"
            },
            {
                "input": "15",
                "expected_output": "1307674368000"
            }
        ],
        "solution": {
            "python": """n = int(input())
result = 1
for i in range(1, n + 1):
    result *= i
print(result)""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        long result = 1;
        for(int i = 1; i <= n; i++) {
            result *= i;
        }
        System.out.println(result);
    }
}""",
            "cpp": """#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    long long result = 1;
    for(int i = 1; i <= n; i++) {
        result *= i;
    }
    cout << result;
    return 0;
}"""
        }
    },
    {
        "id": "q3",
        "title": "Reverse String",
        "difficulty": "easy",
        "description": """
Given a string, reverse it and print the result.

**Input Format:**
- Single line: string s

**Output Format:**
- Single line: reversed string

**Constraints:**
- 1 ≤ length(s) ≤ 1000
""",
        "boilerplate": {
            "python": """s = input()
# Write your solution here
""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        // Write your solution here
    }
}""",
            "cpp": """#include <iostream>
#include <string>
using namespace std;

int main() {
    string s;
    getline(cin, s);
    // Write your solution here
    return 0;
}"""
        },
        "visible_test_cases": [
            {
                "input": "hello",
                "expected_output": "olleh",
                "explanation": "Reverse of 'hello' is 'olleh'"
            },
            {
                "input": "world",
                "expected_output": "dlrow",
                "explanation": "Reverse of 'world' is 'dlrow'"
            }
        ],
        "hidden_test_cases": [
            {
                "input": "a",
                "expected_output": "a"
            },
            {
                "input": "racecar",
                "expected_output": "racecar"
            },
            {
                "input": "Python Programming",
                "expected_output": "gnimmargorP nohtyP"
            }
        ],
        "solution": {
            "python": """s = input()
print(s[::-1])""",
            "java": """import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String s = sc.nextLine();
        System.out.println(new StringBuilder(s).reverse().toString());
    }
}""",
            "cpp": """#include <iostream>
#include <string>
#include <algorithm>
using namespace std;

int main() {
    string s;
    getline(cin, s);
    reverse(s.begin(), s.end());
    cout << s;
    return 0;
}"""
        }
    }
]


def get_question_by_id(question_id: str):
    """Get a question by its ID."""
    for q in EXAMPLE_QUESTIONS:
        if q["id"] == question_id:
            return q
    return None


def get_questions_by_difficulty(difficulty: str):
    """Get all questions of a specific difficulty."""
    return [q for q in EXAMPLE_QUESTIONS if q["difficulty"] == difficulty]


def get_all_questions():
    """Get all questions."""
    return EXAMPLE_QUESTIONS


# Example usage
if __name__ == "__main__":
    print("Example Questions for Assessment System\n")
    print("=" * 60)
    
    for q in EXAMPLE_QUESTIONS:
        print(f"\nID: {q['id']}")
        print(f"Title: {q['title']}")
        print(f"Difficulty: {q['difficulty']}")
        print(f"Visible Test Cases: {len(q['visible_test_cases'])}")
        print(f"Hidden Test Cases: {len(q['hidden_test_cases'])}")
        print(f"Languages: {', '.join(q['boilerplate'].keys())}")
    
    print("\n" + "=" * 60)
    print(f"\nTotal Questions: {len(EXAMPLE_QUESTIONS)}")
