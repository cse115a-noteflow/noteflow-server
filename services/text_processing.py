from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def chunk_notes(notes, title, description, owner_email, chunk_size=1500, overlap=100):
    """Splits text into overlapping chunks."""
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )

        documents = []
        for note in notes:
            chunks = text_splitter.split_text(note)
            for chunk in chunks:
                document = Document(
                    page_content=chunk,
                    metadata={
                        "title": title,
                        "description": description,
                        "owner_email": owner_email,
                    }
                )
                documents.append(document)

        return documents
    except Exception as e:
        print(f"Error chunking text: {e}")
        return []
