import random
from typing import List
from ..schemas.assessment import CodingProblem, MCQQuestion, TestCase


class QuestionBank:
    """Predefined question bank for assessment generation"""
    
    CODING_PROBLEMS = [
        CodingProblem(
            id="coding_1",
            title="Two Sum",
            description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
            input_format="First line: space-separated integers (array)\nSecond line: target integer",
            output_format="Two space-separated indices",
            constraints="2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9",
            boilerplate={
                "python": "def two_sum(nums, target):\n    # Write your code here\n    pass\n\nif __name__ == '__main__':\n    nums = list(map(int, input().split()))\n    target = int(input())\n    result = two_sum(nums, target)\n    print(result[0], result[1])",
                "java": "import java.util.*;\n\npublic class Solution {\n    public static int[] twoSum(int[] nums, int target) {\n        // Write your code here\n        return new int[]{0, 0};\n    }\n    \n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] input = sc.nextLine().split(\" \");\n        int[] nums = new int[input.length];\n        for (int i = 0; i < input.length; i++) {\n            nums[i] = Integer.parseInt(input[i]);\n        }\n        int target = sc.nextInt();\n        int[] result = twoSum(nums, target);\n        System.out.println(result[0] + \" \" + result[1]);\n    }\n}",
                "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\n\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Write your code here\n    return {0, 0};\n}\n\nint main() {\n    string line;\n    getline(cin, line);\n    istringstream iss(line);\n    vector<int> nums;\n    int num;\n    while (iss >> num) nums.push_back(num);\n    int target;\n    cin >> target;\n    vector<int> result = twoSum(nums, target);\n    cout << result[0] << \" \" << result[1] << endl;\n    return 0;\n}"
            },
            visible_test_cases=[
                TestCase(input="2 7 11 15\n9", output="0 1"),
                TestCase(input="3 2 4\n6", output="1 2")
            ],
            hidden_test_cases=[
                TestCase(input="3 3\n6", output="0 1"),
                TestCase(input="1 5 3 7 9\n12", output="2 4"),
                TestCase(input="-1 -2 -3 -4 -5\n-8", output="2 4")
            ]
        ),
        CodingProblem(
            id="coding_2",
            title="Palindrome Check",
            description="Given a string, determine if it is a palindrome (reads the same forward and backward).",
            input_format="Single line: string to check",
            output_format="'true' or 'false'",
            constraints="1 <= s.length <= 10^5",
            boilerplate={
                "python": "def is_palindrome(s):\n    # Write your code here\n    pass\n\nif __name__ == '__main__':\n    s = input().strip()\n    result = is_palindrome(s)\n    print('true' if result else 'false')",
                "java": "import java.util.*;\n\npublic class Solution {\n    public static boolean isPalindrome(String s) {\n        // Write your code here\n        return false;\n    }\n    \n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine();\n        System.out.println(isPalindrome(s) ? \"true\" : \"false\");\n    }\n}",
                "cpp": "#include <iostream>\n#include <string>\nusing namespace std;\n\nbool isPalindrome(string s) {\n    // Write your code here\n    return false;\n}\n\nint main() {\n    string s;\n    getline(cin, s);\n    cout << (isPalindrome(s) ? \"true\" : \"false\") << endl;\n    return 0;\n}"
            },
            visible_test_cases=[
                TestCase(input="racecar", output="true"),
                TestCase(input="hello", output="false")
            ],
            hidden_test_cases=[
                TestCase(input="a", output="true"),
                TestCase(input="ab", output="false"),
                TestCase(input="abba", output="true")
            ]
        ),
        CodingProblem(
            id="coding_3",
            title="Reverse Array",
            description="Given an array of integers, reverse it in-place.",
            input_format="Space-separated integers",
            output_format="Space-separated integers (reversed)",
            constraints="1 <= arr.length <= 10^4",
            boilerplate={
                "python": "def reverse_array(arr):\n    # Write your code here\n    pass\n\nif __name__ == '__main__':\n    arr = list(map(int, input().split()))\n    reverse_array(arr)\n    print(' '.join(map(str, arr)))",
                "java": "import java.util.*;\n\npublic class Solution {\n    public static void reverseArray(int[] arr) {\n        // Write your code here\n    }\n    \n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String[] input = sc.nextLine().split(\" \");\n        int[] arr = new int[input.length];\n        for (int i = 0; i < input.length; i++) {\n            arr[i] = Integer.parseInt(input[i]);\n        }\n        reverseArray(arr);\n        for (int i = 0; i < arr.length; i++) {\n            System.out.print(arr[i]);\n            if (i < arr.length - 1) System.out.print(\" \");\n        }\n    }\n}",
                "cpp": "#include <iostream>\n#include <vector>\n#include <sstream>\nusing namespace std;\n\nvoid reverseArray(vector<int>& arr) {\n    // Write your code here\n}\n\nint main() {\n    string line;\n    getline(cin, line);\n    istringstream iss(line);\n    vector<int> arr;\n    int num;\n    while (iss >> num) arr.push_back(num);\n    reverseArray(arr);\n    for (int i = 0; i < arr.size(); i++) {\n        cout << arr[i];\n        if (i < arr.size() - 1) cout << \" \";\n    }\n    return 0;\n}"
            },
            visible_test_cases=[
                TestCase(input="1 2 3 4 5", output="5 4 3 2 1")
            ],
            hidden_test_cases=[
                TestCase(input="10", output="10"),
                TestCase(input="1 2", output="2 1")
            ]
        )
    ]
    
    MCQ_QUESTIONS = [
        MCQQuestion(
            id="mcq_1",
            question="What is the time complexity of binary search?",
            options=[
                {"id": "A", "text": "O(n)"},
                {"id": "B", "text": "O(log n)"},
                {"id": "C", "text": "O(n^2)"},
                {"id": "D", "text": "O(1)"}
            ],
            correct_answer="B"
        ),
        MCQQuestion(
            id="mcq_2",
            question="Which data structure uses LIFO?",
            options=[
                {"id": "A", "text": "Queue"},
                {"id": "B", "text": "Stack"},
                {"id": "C", "text": "Array"},
                {"id": "D", "text": "Tree"}
            ],
            correct_answer="B"
        ),
        MCQQuestion(
            id="mcq_3",
            question="What is the space complexity of merge sort?",
            options=[
                {"id": "A", "text": "O(1)"},
                {"id": "B", "text": "O(log n)"},
                {"id": "C", "text": "O(n)"},
                {"id": "D", "text": "O(n^2)"}
            ],
            correct_answer="C"
        ),
        MCQQuestion(
            id="mcq_4",
            question="Which sorting algorithm is stable?",
            options=[
                {"id": "A", "text": "Quick sort"},
                {"id": "B", "text": "Heap sort"},
                {"id": "C", "text": "Merge sort"},
                {"id": "D", "text": "Selection sort"}
            ],
            correct_answer="C"
        ),
        MCQQuestion(
            id="mcq_5",
            question="What is a hash collision?",
            options=[
                {"id": "A", "text": "Two keys map to same index"},
                {"id": "B", "text": "Hash function fails"},
                {"id": "C", "text": "Table is full"},
                {"id": "D", "text": "Key not found"}
            ],
            correct_answer="A"
        ),
        MCQQuestion(
            id="mcq_6",
            question="Which traversal visits root first?",
            options=[
                {"id": "A", "text": "Inorder"},
                {"id": "B", "text": "Preorder"},
                {"id": "C", "text": "Postorder"},
                {"id": "D", "text": "Level order"}
            ],
            correct_answer="B"
        ),
        MCQQuestion(
            id="mcq_7",
            question="What is the worst case of quicksort?",
            options=[
                {"id": "A", "text": "O(n log n)"},
                {"id": "B", "text": "O(n)"},
                {"id": "C", "text": "O(n^2)"},
                {"id": "D", "text": "O(log n)"}
            ],
            correct_answer="C"
        ),
        MCQQuestion(
            id="mcq_8",
            question="Which is NOT a graph traversal?",
            options=[
                {"id": "A", "text": "BFS"},
                {"id": "B", "text": "DFS"},
                {"id": "C", "text": "Dijkstra"},
                {"id": "D", "text": "Binary search"}
            ],
            correct_answer="D"
        ),
        MCQQuestion(
            id="mcq_9",
            question="What is dynamic programming?",
            options=[
                {"id": "A", "text": "Divide and conquer"},
                {"id": "B", "text": "Memoization + optimal substructure"},
                {"id": "C", "text": "Greedy approach"},
                {"id": "D", "text": "Backtracking"}
            ],
            correct_answer="B"
        ),
        MCQQuestion(
            id="mcq_10",
            question="Which has O(1) average insertion?",
            options=[
                {"id": "A", "text": "Array"},
                {"id": "B", "text": "Linked list"},
                {"id": "C", "text": "Hash table"},
                {"id": "D", "text": "Binary tree"}
            ],
            correct_answer="C"
        ),
        MCQQuestion(
            id="mcq_11",
            question="What is a balanced BST?",
            options=[
                {"id": "A", "text": "Height difference <= 1"},
                {"id": "B", "text": "All leaves at same level"},
                {"id": "C", "text": "Complete binary tree"},
                {"id": "D", "text": "Perfect binary tree"}
            ],
            correct_answer="A"
        ),
        MCQQuestion(
            id="mcq_12",
            question="Which is NOT a stable sort?",
            options=[
                {"id": "A", "text": "Merge sort"},
                {"id": "B", "text": "Insertion sort"},
                {"id": "C", "text": "Quick sort"},
                {"id": "D", "text": "Bubble sort"}
            ],
            correct_answer="C"
        )
    ]
    
    @classmethod
    def generate_assessment(cls, candidate_id: int) -> dict:
        """Generate unique assessment using candidate_id as seed"""
        random.seed(candidate_id)
        
        # Select 2 coding problems
        coding = random.sample(cls.CODING_PROBLEMS, 2)
        
        # Select 10 MCQs
        mcq = random.sample(cls.MCQ_QUESTIONS, 10)
        
        return {
            "coding": [problem.dict() for problem in coding],
            "mcq": [question.dict() for question in mcq]
        }
