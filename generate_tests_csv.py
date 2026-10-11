import csv
from pathlib import Path

DOCS_DIR = Path("./docs")

tests_data = [
    # --------------------------------------------------------------------------
    # DEV SPLIT (10 questions: 7 answerable, 3 refusals)
    # --------------------------------------------------------------------------
    {
        "id": 1,
        "split": "dev",
        "question": "Can I write my semester-end exams if my attendance is only 70% as an undergraduate student?",
        "expected_source": "attendance_regulations.md",
        "expected_keywords": "75%",
        "should_refuse": 0,
        "evidence_file": "attendance_regulations.md",
        "evidence_line": 10,
        "evidence_quote": "- 75% attendance (60% without co-curricular) is mandatory to take up the End Semester Examination (ESE)."
    },
    {
        "id": 2,
        "split": "dev",
        "question": "What happens if a student has less than 35% attendance in all subjects of a semester?",
        "expected_source": "attendance_regulations.md",
        "expected_keywords": "35%;repeat",
        "should_refuse": 0,
        "evidence_file": "attendance_regulations.md",
        "evidence_line": 12,
        "evidence_quote": "- Student with less than 35% attendance each in all the subjects of a semester will have to repeat that semester again."
    },
    {
        "id": 3,
        "split": "dev",
        "question": "Is it permitted to make phone calls or use mobile devices during lectures?",
        "expected_source": "code_of_conduct.md",
        "expected_keywords": "banned",
        "should_refuse": 0,
        "evidence_file": "code_of_conduct.md",
        "evidence_line": 56,
        "evidence_quote": "-  Use of mobiles in classrooms is banned."
    },
    {
        "id": 4,
        "split": "dev",
        "question": "What types of T-shirts are prohibited for boys under the dress code?",
        "expected_source": "code_of_conduct.md",
        "expected_keywords": "round neck;v-neck",
        "should_refuse": 0,
        "evidence_file": "code_of_conduct.md",
        "evidence_line": 82,
        "evidence_quote": "-  Round Neck or V-Neck T-shirts of any kind, particularly those with Graphic Prints,"
    },
    {
        "id": 5,
        "split": "dev",
        "question": "Within how many working days must a student apply for photocopy or revaluation of results?",
        "expected_source": "results_and_revaluation.md",
        "expected_keywords": "5 working days",
        "should_refuse": 0,
        "evidence_file": "results_and_revaluation.md",
        "evidence_line": 14,
        "evidence_quote": "- Request for photocopy/revaluation/challenge valuation by the students should be made to the Controller of Examinations within 5 working days from the date of publishing of results along with the prescribed fee and after revaluation, the higher marks will be considered."
    },
    {
        "id": 6,
        "split": "dev",
        "question": "What is the minimum mark in ESE required for a student to apply for revaluation?",
        "expected_source": "results_and_revaluation.md",
        "expected_keywords": "25%",
        "should_refuse": 0,
        "evidence_file": "results_and_revaluation.md",
        "evidence_line": 16,
        "evidence_quote": "- Students can apply for Revaluation only if they score a minimum 25% marks in the ESE."
    },
    {
        "id": 7,
        "split": "dev",
        "question": "For postgraduate (PG) students, what overall semester average is required to be declared passed?",
        "expected_source": "attendance_regulations.md",
        "expected_keywords": "50%",
        "should_refuse": 0,
        "evidence_file": "attendance_regulations.md",
        "evidence_line": 38,
        "evidence_quote": "- Along with a semester average of 50%"
    },
    {
        "id": 8,
        "split": "dev",
        "question": "What is the fee refund policy if a student cancels their admission after the commencement of classes?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    },
    {
        "id": 9,
        "split": "dev",
        "question": "What was the highest package offered during the 2025 college placement drive?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    },
    {
        "id": 10,
        "split": "dev",
        "question": "What is the annual tuition fee for the Bachelor of Science in Computer Science program?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    },

    # --------------------------------------------------------------------------
    # TEST SPLIT (10 questions: 7 answerable, 3 refusals)
    # --------------------------------------------------------------------------
    {
        "id": 11,
        "split": "test",
        "question": "What minimum attendance percentage do master's students need to maintain in each theory and practical subject?",
        "expected_source": "attendance_regulations.md",
        "expected_keywords": "80%",
        "should_refuse": 0,
        "evidence_file": "attendance_regulations.md",
        "evidence_line": 16,
        "evidence_quote": "- Students are required to maintain a minimum attendance of 80% in each paper, for both theory & practicals. Students having less than 80% attendance in a paper will not be eligible to write the End Semester Examination for that paper."
    },
    {
        "id": 12,
        "split": "test",
        "question": "What is the general formula for the maximum time span allowed to complete a degree?",
        "expected_source": "results_and_revaluation.md",
        "expected_keywords": "N + 3",
        "should_refuse": 0,
        "evidence_file": "results_and_revaluation.md",
        "evidence_line": 34,
        "evidence_quote": "Time Span to complete the degree = N + 3 years."
    },
    {
        "id": 13,
        "split": "test",
        "question": "Within how many working days must the Grievance Redressal Committee attend to written grievances from students?",
        "expected_source": "grievance_redressal_policy.md",
        "expected_keywords": "three working days",
        "should_refuse": 0,
        "evidence_file": "grievance_redressal_policy.md",
        "evidence_line": 104,
        "evidence_quote": "The issues will be attended promptly on receipt of written grievances from the students within three working days. The Grievance committee will act upon those cases which have been forwarded along with the necessary documents."
    },
    {
        "id": 14,
        "split": "test",
        "question": "What is the official email address for the Students Grievance Redressal Committee?",
        "expected_source": "grievance_redressal_policy.md",
        "expected_keywords": "grievancestudents@mccblr.edu.in",
        "should_refuse": 0,
        "evidence_file": "grievance_redressal_policy.md",
        "evidence_line": 52,
        "evidence_quote": "1. Students Grievance Redressal Committee: grievancestudents@mccblr.edu.in"
    },
    {
        "id": 15,
        "split": "test",
        "question": "How is the grading split between internal continuous assessment and end-of-semester theory exams?",
        "expected_source": "continuous_internal_assessment.md",
        "expected_keywords": "40 : 60",
        "should_refuse": 0,
        "evidence_file": "continuous_internal_assessment.md",
        "evidence_line": 14,
        "evidence_quote": "Total marks for each course shall be based on continuous assessments and semester end examinations. As per the decision taken at the Karnataka State Higher Education Council, it is necessary to have uniform pattern of 40 : 60 for IA and Semester End Theory Examinations respectively and 50 : 50 for IA and Semester End Practical Examinations respectively, in all the Universities, their Affiliated and Autonomous Colleges."
    },
    {
        "id": 16,
        "split": "test",
        "question": "What is the duration of the End Semester Examination theory paper for NEP batch students?",
        "expected_source": "end_semester_examinations.md",
        "expected_keywords": "2 ½ Hours",
        "should_refuse": 0,
        "evidence_file": "end_semester_examinations.md",
        "evidence_line": 18,
        "evidence_quote": "| Duration of Theory / Practical Paper | 3 Hours | 2 ½ Hours | 3 Hours"
    },
    {
        "id": 17,
        "split": "test",
        "question": "What academic condition must a UG candidate satisfy to be permitted to enter the Fifth Semester?",
        "expected_source": "promotion_and_awards.md",
        "expected_keywords": "50% of the papers",
        "should_refuse": 0,
        "evidence_file": "promotion_and_awards.md",
        "evidence_line": 12,
        "evidence_quote": "- A candidate will be permitted to go to the Fifth Semester provided she has passed overall in 50% of the papers of Part I, II & III of the First and Second Semesters."
    },
    {
        "id": 18,
        "split": "test",
        "question": "What are the operating hours and equipment reservation rules for the campus gymnasium?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    },
    {
        "id": 19,
        "split": "test",
        "question": "How many physical books is an undergraduate student permitted to borrow from the library simultaneously?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    },
    {
        "id": 20,
        "split": "test",
        "question": "What is the monthly hostel mess fee and curfew schedule at Mother Mary Memorial Hostel?",
        "expected_source": "",
        "expected_keywords": "I don't know based on the provided documents.",
        "should_refuse": 1,
        "evidence_file": "",
        "evidence_line": "",
        "evidence_quote": ""
    }
]

# Strict Verification of all evidence lines against files
for row in tests_data:
    if row["should_refuse"] == 0:
        filepath = DOCS_DIR / row["evidence_file"]
        lines = filepath.read_text(encoding="utf-8").splitlines()
        line_num = int(row["evidence_line"])
        actual_line = lines[line_num - 1]
        assert row["evidence_quote"] in actual_line or actual_line in row["evidence_quote"], f"Mismatch in {row['evidence_file']} line {line_num}:\nExpected: {row['evidence_quote']}\nActual: {actual_line}"

# Write tests.csv
fieldnames = ["id", "split", "question", "expected_source", "expected_keywords", "should_refuse", "evidence_file", "evidence_line", "evidence_quote"]
with open("tests.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(tests_data)

print("Regenerated tests.csv successfully with 20 updated test cases.")
