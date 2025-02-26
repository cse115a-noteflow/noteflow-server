from pinecone import Pinecone
import time
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from config import PINECONE_API_KEY, OPENAI_API_KEY

INDEX_NAME = "noteflow"

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(INDEX_NAME)

# Initialize OpenAI Embeddings
embeddings = OpenAIEmbeddings(
    model = "text-embedding-3-small",
    openai_api_key = OPENAI_API_KEY,)

def delete_note_vectors(note_id):
    """Deletes the note vectors from Pinecone"""
    try:
        response = index.delete(namespace=note_id, delete_all=True)

        if response == {}:
            print(f"Successfully deleted vectors for note {note_id}")
        else:
            print(f"Namespace {note_id} not found or already empty.")
    except Exception as e:
        if "Namespace not found" in str(e):
            print(f"Namespace {note_id} does not exist. Skipping deletion.")
    

def save_note_vectors(note_id, note_chunks):
    """Embeds and saves note chunks in Pinecone"""
    # Seeing index stats before upsert
    print("Index before upsert:")
    print(pc.Index(INDEX_NAME).describe_index_stats())
    print("\n")
    try:
        delete_note_vectors(note_id)
        
        # Save note chunks in Pinecone
        PineconeVectorStore.from_documents(
            documents=note_chunks,
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=note_id,
        )
        
        time.sleep(1) # Wait for the index to update, sometimes takes more than 1 second
        print("Index after upsert:")
        print(pc.Index(INDEX_NAME).describe_index_stats())
        print("\n")
    except Exception as e:
        print(f"Error saving note vectors: {e}")  
    
def retrieve_similar_notes(query, note_id, top_k=3):
    """Retrieves top-k similar notes from Pinecone"""
    # Compare query vector to all note vectors in Pinecone with same note_id
    query_vector = embeddings.embed_query(query)
    context = index.query(
        vector=query_vector,
        namespace=note_id,
        top_k=top_k,
        include_values=True,
        include_metadata=True,
    )

    context_text = ""
    for match in context['matches']:
        context_text += match['metadata']['text']
        
    return context_text