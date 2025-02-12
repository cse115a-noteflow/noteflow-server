import openai
from openai import OpenAI
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key = OPENAI_API_KEY)


def query_llm(query, context, model="gpt-4o", top_k = 3):
    """Generate response from LLM using retrieved context."""
    
    prompt = f'''
    You are an intelligent assistant that answers questions **only** based on the provided context on the note document.
    Do **not** use prior knowledge. If the note document context does not contain enough information to answer the question, say:
    "Your document(s) do not provide an answer to this question."
    Document Context:
    {context}

    ---
    Question:
    {query}

    '''
    try:
        response = client.chat.completions.create(
            model = model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error querying LLM: {e}"