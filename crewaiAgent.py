from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from openai import OpenAI as OpenAIClient
import json
from typing import List, Dict

# Initialize OpenAI client with DeepInfra API
deepinfra_client = OpenAIClient(
    api_key="syXAj0o7cJOXa3hM4lVf6sOQqrXR1WYj",
    base_url="https://api.deepinfra.com/v1/openai"
)

# Custom LLM wrapper for DeepInfra
class DeepInfraLLM:
    def __init__(self, model: str):
        self.model = model

    def _call(self, prompt: str) -> str:
        response = deepinfra_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def __call__(self, prompt: str) -> str:
        return self._call(prompt)

# Define the HTML content search tool
def search_html_content(query: str, html_content_array: List[str]) -> str:
    """Tool to search and extract content from an array of HTML strings."""
    html_input = "\n\n---\n\n".join(html_content_array)
    prompt = (
        f"You are an expert in HTML content extraction. Given the following HTML content:\n\n"
        f"{html_input}\n\n"
        f"Extract the content matching this query: '{query}'. "
        "Return only the matching HTML content in its original structure inside Markdown code blocks. "
        "Ignore empty or irrelevant elements like <p></p>. If multiple sections match, return each in separate code blocks."
    )
    response = deepinfra_client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Create a simple custom agent
class HTMLSearchAgent:
    def __init__(self, html_content_array: List[str]):
        """Initialize the agent with an array of HTML content."""
        self.html_content_array = html_content_array
        self.llm = DeepInfraLLM(model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
        
        # Define the tool
        self.tool = Tool(
            name="HTML_Content_Search",
            func=lambda q: search_html_content(q, self.html_content_array),
            description="Search and extract specific content from an array of HTML documents based on a query."
        )

    def query(self, user_query: str) -> Dict[str, str]:
        """Process a user query and return the extracted content."""
        try:
            # Directly call the tool with the query
            result = self.tool.func(user_query)
            return {
                "message": "Data received",
                "data": result,
                "status": "success"
            }
        except Exception as e:
            return {
                "message": "Error occurred",
                "data": str(e),
                "status": "failure"
            }

    def run_interactive(self):
        """Run an interactive session with the agent."""
        print("Start querying the HTML content (type 'exit' to end).")
        while True:
            query = input("Enter your query (e.g., 'extract paragraph 2' or 'find table with sales'): ")
            if query.lower() == 'exit':
                print("Exiting...")
                break
            result = self.query(query)
            print(f"Response: {result['data']}")

# Example usage
if __name__ == "__main__":
    # Sample HTML content array
    html_content_array = [
        '<div><p>This is the first paragraph.</p><p></p><p>Second paragraph here.</p></div>',
        '<table><tr><th>Sales</th><td>100</td></tr><tr><th>Profit</th><td>20</td></tr></table>',
        '<ul><li>Item 1</li><li>Item 2</li></ul><p>Another paragraph.</p>'
    ]

    # Initialize the agent
    agent = HTMLSearchAgent(html_content_array)

    # Run the interactive session
    agent.run_interactive()