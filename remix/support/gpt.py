"""
GPT support module for content remixing.
Provides basic GPT completion functionality using OpenAI API.
"""

import sys
import os

# Add the parent directory to the path to import admin.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from admin import OPENAI_KEY, model
from openai import OpenAI


def chat_completion(prompt: str, system_message: str = "You are a helpful assistant.") -> str:
    """
    Basic chat completion function using OpenAI GPT.
    
    Args:
        prompt: The user prompt to send to GPT
        system_message: System message to guide the assistant behavior
        
    Returns:
        str: The GPT response
    """
    try:
        # Initialize OpenAI client (new API v1.0+)
        client = OpenAI(api_key=OPENAI_KEY)

        # Create chat completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error in GPT completion: {str(e)}")
        return f"Error generating content: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Test the function
    test_prompt = "Write a short social media post about AI technology."
    result = chat_completion(test_prompt)
    print("GPT Response:")
    print(result)
