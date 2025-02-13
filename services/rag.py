from services.vectorstore_service import delete_note_vectors, save_note_vectors, retrieve_similar_notes
from services.llm_service import query_llm
from services.text_processing import chunk_notes

def rag_store(note_data):
    """ Embeds and stores a note in Pinecone """
    # Processing the document
    note_id = note_data["id"]
    if not note_id:
        return False
    
    title = note_data["title"]
    description = note_data["description"]
    owner_email = note_data["owner"]
    text_blocks = [" ".join(
        block["value"]
        for block in note_data.get("content", [])
        if block.get("value", "").strip()
    )]
    
    # Chunking the document
    note_chunks = chunk_notes(text_blocks, title, description, owner_email)
    
    # Create embeddings and store in Pinecone
    save_note_vectors(note_id, note_chunks)

    return True

def rag_remove(note_id):
    """Removes all document vectors from Pinecone by note ID."""
    if not note_id:
        return False

    # Delete vectors from Pinecone
    delete_note_vectors(note_id)

    return True

def rag_query(query, note_id):
    """Handles user query using RAG pipeline."""
    if not query or not note_id:
        return None

    context = retrieve_similar_notes(query, note_id, top_k = 3)
    response = query_llm(query, context)

    return response

        