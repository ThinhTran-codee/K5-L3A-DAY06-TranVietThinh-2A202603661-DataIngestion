import json
import csv
import re
from pathlib import Path
import pypdf

pdf_path = 'starter/data/Introduction_To_Computer_Science_-_WEB.pdf'
reader = pypdf.PdfReader(pdf_path)

def normalize_text(t: str) -> str:
    # replace special apostrophes/quotes with standard ones and collapse whitespaces
    t = t.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def get_page_text_norm(p: int) -> str:
    raw = reader.pages[p-1].extract_text() or ''
    return normalize_text(raw)

questions = [
    # Dev: 15 questions (q01 to q15)
    {
        "id": "q01",
        "type": "direct",
        "split": "dev",
        "question": "What mathematical technique did Richard Bellman invent in 1953 to solve complex problems?",
        "expected_answer": "Dynamic programming",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 22,
        "evidence_quote": "In 1953, Bellman invented dynamic programming,1 which is a mathematical optimization methodology and a technique for computer programming.",
        "filter": None
    },
    {
        "id": "q02",
        "type": "direct",
        "split": "dev",
        "question": "Why is the ENIAC notable in computer history?",
        "expected_answer": "It was the first general-purpose computer that could run any program specified by a programmer.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 23,
        "evidence_quote": "ENIAC is notable in computer history because it was the first general-purpose computer, meaning that it could run not just a single program but rather any program specified by a programmer.",
        "filter": None
    },
    {
        "id": "q03",
        "type": "condition_exception",
        "split": "dev",
        "question": "What is an example of a task that neither computers nor humans can perform?",
        "expected_answer": "Accurately predicting chaotic systems like long-term weather patterns.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 25,
        "evidence_quote": "On the flip side, there are tasks that neither computers nor humans can perform, such as accurately predicting chaotic systems like long-term weather patterns.",
        "filter": None
    },
    {
        "id": "q04",
        "type": "direct",
        "split": "dev",
        "question": "What early computer network, circa 1974, was an early predecessor to the Internet?",
        "expected_answer": "The ARPANET",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 23,
        "evidence_quote": "The ARPANET, circa 1974, was an early predecessor to the Internet. It allowed computers at Pentagon-funded research facilities to communicate over phone lines.",
        "filter": None
    },
    {
        "id": "q05",
        "type": "paraphrase",
        "split": "dev",
        "question": "How do cooking recipes exemplify algorithmic procedures in computer science?",
        "expected_answer": "Recipes are algorithms with precise directions for ingredient amounts, combination steps, and cooking methods.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 21,
        "evidence_quote": "recipes to prepare food are algorithms with precise directions for ingredient amounts, the process to combine these, and the temperatures and cooking methods needed to transform the combined ingredients into a specific dish.",
        "filter": None
    },
    {
        "id": "q06",
        "type": "direct",
        "split": "dev",
        "question": "By what percentage does the U.S. Bureau of Labor Statistics project jobs for computer research scientists to grow by 2033?",
        "expected_answer": "26%",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 28,
        "evidence_quote": "by 2033, the number of jobs available for computer and information research scientists is expected to increase by 26%.",
        "filter": None
    },
    {
        "id": "q07",
        "type": "condition_exception",
        "split": "dev",
        "question": "Under what condition do spreadsheets become prone to data management problems?",
        "expected_answer": "The more data and the more people involved in a spreadsheet.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 31,
        "evidence_quote": "The more data and the more people involved in a spreadsheet, the greater the potential for spreadsheet problems.",
        "filter": None
    },
    {
        "id": "q08",
        "type": "direct",
        "split": "dev",
        "question": "What discipline emphasizes experimentation and evaluation of the boundary between humans and computers?",
        "expected_answer": "Human-computer interaction (HCI)",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 33,
        "evidence_quote": "Science plays a key role in human-computer interaction, which emphasizes experimentation and evaluation of the interface (boundary) between humans and computers",
        "filter": None
    },
    {
        "id": "q09",
        "type": "direct",
        "split": "dev",
        "question": "What is an adversarial attack in machine learning?",
        "expected_answer": "Sample input designed to cause a system to behave unexpectedly, incorrectly, or inappropriately.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 43,
        "evidence_quote": "adversarial attack sample input (e.g., an image) that is designed to cause a system to behave problematically",
        "filter": None
    },
    {
        "id": "q10",
        "type": "direct",
        "split": "dev",
        "question": "What ethical obligation do computer scientists have regarding technological knowledge?",
        "expected_answer": "An obligation to be ethical and good stewards of technology with an emphasis on responsible computing.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 36,
        "evidence_quote": "Computer scientists have an obligation to be ethical and good stewards of technology with an emphasis on responsible computing.",
        "filter": None
    },
    {
        "id": "q11",
        "type": "metadata_filter",
        "split": "dev",
        "question": "In section 1.1 Computer Science, what visa category helps U.S. employers address technology worker shortages?",
        "expected_answer": "H-1B visas",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 28,
        "evidence_quote": "To fill some of these jobs, U.S. employers likely will continue to rely on H-1B visas.",
        "filter": {"section": "1.1 Computer Science"}
    },
    {
        "id": "q12",
        "type": "metadata_filter",
        "split": "dev",
        "question": "In the Chapter 1 Review, how is big data defined?",
        "expected_answer": "Very large datasets that aren't easily processed using spreadsheets.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 43,
        "evidence_quote": "big data very large datasets that aren't easily processed using spreadsheets",
        "filter": {"section": "Chapter 1 Review"}
    },
    {
        "id": "q13",
        "type": "paraphrase",
        "split": "dev",
        "question": "How does Al Aho describe the concept of computational thinking?",
        "expected_answer": "The thought processes involved in formulating problems so their solutions can be represented as computational steps and algorithms.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 51,
        "evidence_quote": 'describes computational thinking as "the thought processes involved in formulating problems so their solutions can be represented as computational steps and algorithms."',
        "filter": None
    },
    {
        "id": "q14",
        "type": "direct",
        "split": "dev",
        "question": "What is the definition of decomposition in computational thinking?",
        "expected_answer": "Systematically breaking down a complex problem or system into smaller, more manageable parts or subproblems.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 53,
        "evidence_quote": "Decomposition is a fundamental concept in computational thinking, representing the process of systematically breaking down a complex problem or system into smaller, more manageable parts or subproblems.",
        "filter": None
    },
    {
        "id": "q15",
        "type": "direct",
        "split": "dev",
        "question": "How does pattern recognition assist the decomposition process when instructing a robot to prepare a dish?",
        "expected_answer": "It groups identified features into categories such as ingredients, equipment, and actions.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 54,
        "evidence_quote": "Pattern recognition makes it possible to group all the different features considered in decomposition into categories.",
        "filter": None
    },

    # Test: 5 questions (q16 to q20)
    {
        "id": "q16",
        "type": "direct",
        "split": "test",
        "question": "What physical technology did the ENIAC use instead of silicon?",
        "expected_answer": "Vacuum tubes",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 23,
        "evidence_quote": "Instead of silicon, the ENIAC used the technology of a vacuum tube, a physical device like a light bulb that was used as memory in early digital computers.",
        "filter": None
    },
    {
        "id": "q17",
        "type": "condition_exception",
        "split": "test",
        "question": "Why did the One Laptop per Child (OLPC) educational vision fail to truly materialize?",
        "expected_answer": "Children often used the computers for entertainment rather than the learning experiences intended, without adequate educational infrastructure.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 29,
        "evidence_quote": "OLPC's vision for education never truly materialized because children often used the computers for their own entertainment rather than the learning experiences",
        "filter": None
    },
    {
        "id": "q18",
        "type": "paraphrase",
        "split": "test",
        "question": "What role does scientific evaluation play in human-computer interaction (HCI)?",
        "expected_answer": "It emphasizes experimentation and evaluation of the interface between humans and computers to design better computer systems.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 33,
        "evidence_quote": "emphasizes experimentation and evaluation of the interface (boundary) between humans and computers, often toward designing better computer systems.",
        "filter": None
    },
    {
        "id": "q19",
        "type": "metadata_filter",
        "split": "test",
        "question": "In section 2.1 Computational Thinking, what does decomposition involve when tackling complex problems?",
        "expected_answer": "Solving a complex problem by breaking it up into smaller, more manageable tasks.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 54,
        "evidence_quote": "Decomposition involves solving a complex problem by breaking it up into smaller, more manageable tasks.",
        "filter": {"section": "2.1 Computational Thinking"}
    },
    {
        "id": "q20",
        "type": "direct",
        "split": "test",
        "question": "In the Chapter 1 Review, how is a spreadsheet defined?",
        "expected_answer": "A data-centric programming environment where data is organized into cells in a table.",
        "gold_source_id": "openstax-intro-cs",
        "gold_page": 43,
        "evidence_quote": "spreadsheet data-centric programming environment where data is organized into cells in a table",
        "filter": None
    }
]

print("--- Checking evidence quotes match ---")
all_matched = True
for q in questions:
    p = q["gold_page"]
    page_txt = get_page_text_norm(p)
    quote_norm = normalize_text(q["evidence_quote"])
    # store normalized quote
    q["evidence_quote"] = quote_norm
    if quote_norm in page_txt:
        print(f"[{q['id']}] PASS (p.{p})")
    else:
        print(f"[{q['id']}] FAILED on p.{p}!")
        print("Target quote:", repr(quote_norm))
        # inspect snippet
        words = quote_norm.split()[:4]
        match_idx = page_txt.find(" ".join(words))
        if match_idx != -1:
            print("Found nearby:", page_txt[match_idx:match_idx+len(quote_norm)+20])
        all_matched = False

if all_matched:
    print("\nSUCCESS: All 20 quotes verified 100% against extracted text!")
    Path("benchmark").mkdir(exist_ok=True)
    with open("benchmark/benchmark.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    # Also save CSV for easy reading
    with open("benchmark/benchmark.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "split", "type", "question", "expected_answer", "gold_source_id", "gold_page", "evidence_quote", "filter"])
        writer.writeheader()
        for q in questions:
            row = dict(q)
            row["filter"] = json.dumps(row["filter"]) if row["filter"] else ""
            writer.writerow(row)
    print("Saved benchmark/benchmark.json and benchmark/benchmark.csv")
else:
    print("\nFAILED: Fix quote differences before proceeding.")
