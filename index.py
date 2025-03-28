from openai import OpenAI
import json
import re

# Initialize OpenAI client
openai = OpenAI(
    api_key="syXAj0o7cJOXa3hM4lVf6sOQqrXR1WYj",
    base_url="https://api.deepinfra.com/v1/openai"
)

# Initialize conversation history
# conversation_history = [
#     {
#         "role": "system",
#         "content": (
#             """You will be given an HTML document representing a multi-page document. Your task is to accurately detect and extract complete content sections, such as paragraphs, tables, lists, or specific sections, while preserving their original HTML structure, styles, and attributes. 

#             Ensure that:  
#             - Content remains in its original format without modifications.  
#             - Empty or irrelevant `<p>` tags and other non-informative elements are ignored.  
#             - If a logical unit of text is split across multiple elements due to formatting, it should be combined appropriately.  
#             - When extracting numbered or requested content, return only the specific section while maintaining structural integrity.  

#             Do not include explanations, additional text, or formatting alterations. The response should only contain the extracted content inside proper code blocks, ensuring compatibility with Markdown parsers.
#         """)
#     }
# ]


# Function to send a message and get a response
def send_message(html_contents , query):
    # Append the user's message to the conversation history
    # conversation_history.append({"role": "user", "content": user_message})

    # Send the request to the OpenAI API
    chat_completion = openai.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        messages=[{"role": "user", "content": f'''Carefully search through the following HTML contents 
            and find the most relevant piece matching this query: "{query}"
            
            HTML Contents to search:
            {html_contents}
            
            Requirements:
            1. Analyze each HTML content thoroughly
            2. Identify the most contextually relevant match
            3. Return ONLY the ENTIRE matching p TAG, not just the HTML content 
            4. To identify the HTML content provide the content inside ```html ```` block
            4. If no clear match exists, return an empty string'''}],
    )

    # Get the assistant's response
    assistant_message = chat_completion.choices[0].message.content
    print(f"Assistant: {assistant_message}")
    assistant_message = re.sub(r"<think>.*?</think>", "", assistant_message, flags=re.DOTALL).strip()
    html = assistant_message.split('```')[1].replace('html\n', '')
    print("8***8888888888888888888888888*****************************************************" , html)
    return {
        "message": "Data received",
        "data": assistant_message,
        "success": True if html else False,

    }

# Start an interactive loop for chatting
print("Start chatting with the assistant (type 'exit' to end the conversation).")

