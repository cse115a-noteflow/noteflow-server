import openai
from openai import OpenAI
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key = OPENAI_API_KEY)


def query_llm(query, context, prompt=None, model="gpt-4o", top_k = 3):
    """Generate response from LLM using retrieved context."""

    if prompt is None:
        prompt = f'''
        You are an intelligent assistant that answers questions **only** based on the provided context on the note.
        Do **not** use prior knowledge. If the note context does not contain enough information to answer the question, say:
        "Your note does not provide an answer to this question."
        Note Context:
        {context}

        ---
        Question:
        {query}

        '''
    else:
        prompt += f"{context}\n\n---\n\n{query}\n\n"
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