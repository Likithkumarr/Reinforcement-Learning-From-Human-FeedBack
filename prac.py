import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

client=AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# feedback_file = "feedbackllm.json"
feedback_file = "feedback3.json"

print("====RLHF LLM Trainer====")
print("Type 'exit' to quit.")

# while True:
#     question = input("ask a question:")
#     if question.lower() == "exit":
#         print("Exiting RLHF LLM Trainer.")
#         break

#     response = client.chat.completions.create(
#         model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
#         messages=[{"role": "user", "content": question}],
#         max_tokens=100
#     )
#     answer = response.choices[0].message.content.strip()
#     print("LLM Response:", answer)

#     feedback = input("Is this response good? (Y/N): ").upper()
#     while feedback not in ["Y", "N"]:
#         feedback = input("Invalid input. Please enter 'Y' or 'N': ").upper()

#     feedback_data = {
#         "question": question,
#         "response": answer,
#         "feedback": feedback
#     }
#     if not os.path.exists(feedback_file):
#         open(feedback_file, 'w').close()  # Create the file if it doesn't exist
#     with open(feedback_file, 'a') as f:
#         json.dump(feedback_data, f)
#         f.write('\n')  # Add a newline after each entry

#     print("Feedback recorded. Thank you!\n")

def generate_response(question):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[{"role": "user", "content": question}],
        max_tokens=100
    )
    return response.choices[0].message.content.strip()

while True:
    question = input("ask a question:")
    if question.lower() == "exit":
        print("Exiting RLHF LLM Trainer.")
        break
    
    while True:
        response = generate_response(question)
        print("LLM Response:", response)

        feedback = input("Is this response good? (Y/N): ").upper()
        while feedback not in ["Y", "N"]:
            feedback = input("Invalid input. Please enter 'Y' or 'N': ").upper()

        # feedback_data = {
        #     "question": question,
        #     "response": response,
        #     "feedback": feedback
        # }
        # if not os.path.exists(feedback_file):
        #     open(feedback_file, 'w').close()  # Create the file if it doesn't exist
        # with open(feedback_file, 'a') as f:
        #     json.dump(feedback_data, f)
        #     f.write('\n')  # Add a newline after each entry        
        # if feedback == "Y":
        #     print("Feedback recorded. Thank you!\n")
        #     break  # Exit the loop if the response is good
        # else:
        #     print("Regenerating response...")
        if feedback == "Y":
            feedback_data = {
                "question": question,
                "response": response,
                "feedback": feedback
            }
            if not os.path.exists(feedback_file):
                open(feedback_file, 'w').close()  # Create the file if it doesn't exist
            with open(feedback_file, 'a') as f:
                json.dump(feedback_data, f)
                f.write('\n')  # Add a newline after each entry
            print("Feedback recorded. Thank you!\n")
            break  # Exit the loop if the response is good
        else:
            print("Regenerating response...")