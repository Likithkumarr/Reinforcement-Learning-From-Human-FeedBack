import random
import json
import os

responses=[
    "Artificial intelligence is the simulation of human intelligence processes by machines, especially computer systems.",
    "AI allows computers to perform tasks that typically require human intelligence, such as visual perception, speech recognition, decision-making, and language translation.",
    "ai enables machines to learn from experience, adapt to new inputs, and perform tasks without explicit programming.",
    "artificial intelligence is a branch of computer science that focuses on creating intelligent machines that can mimic human behavior and cognitive functions.",
]

feedback_file = "feedback.json"

print("====RLHF Chatbot Trainer====")
print("Type 'exit' to quit.")

while True:
    question = input("ask a question:")
    if question.lower() == "exit":
        print("Exiting RLHF Chatbot Trainer.")
        break
    r1, r2 = random.sample(responses, 2)
    print("Response A:", r1)
    print("Response B:", r2)

    feedback = input("Which response is better? (A/B): ").upper()
    while feedback not in ["A", "B"]:
        feedback = input("Invalid input. Please enter 'A' or 'B': ").upper()

    feedback_data = {
        "question": question,
        "response_a": r1,
        "response_b": r2,
        "feedback": feedback
    }
    
    if not os.path.exists(feedback_file):
        open(feedback_file, 'w').close()  # Create the file if it doesn't exist
    with open(feedback_file, 'a') as f:
        json.dump(feedback_data, f)
        f.write('\n')  # Add a newline after each entry

    print("Feedback recorded. Thank you!\n")