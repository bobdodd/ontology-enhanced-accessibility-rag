# app.py

import streamlit as st
import os
import logging
import json
from datetime import datetime
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
DOC_PATH = "./data/3468264.3468581.pdf"
MODEL_NAME = "llama3.1:8b"
EMBEDDING_MODEL = "mxbai-embed-large:v1"
VECTOR_STORE_NAME = "simple-rag"
PERSIST_DIRECTORY = "./chroma_db"
DOCUMENTS_METADATA_FILE = "./chroma_db/documents_metadata.json"


def ingest_pdf(doc_path, title_prefix="", authors="", acm_reference=""):
    """Load PDF documents."""
    if os.path.exists(doc_path):
        loader = UnstructuredPDFLoader(file_path=doc_path)
        data = loader.load()
        logging.info(f"PDF loaded successfully: {doc_path}")

        # Build content prefix with available metadata
        content_prefix = ""
        if title_prefix:
            content_prefix += f"Title: {title_prefix}. "
        if authors:
            content_prefix += f"Authors: {authors}. "
        if acm_reference:
            content_prefix += f"ACM Reference: {acm_reference}. "
        
        if content_prefix:
            data[0].page_content = content_prefix + data[0].page_content
        
        # Add metadata
        data[0].metadata.update({
            "source": doc_path,
            "added_at": datetime.now().isoformat(),
            "title": title_prefix or os.path.basename(doc_path),
            "authors": authors,
            "acm_reference": acm_reference
        })

        return data
    else:
        logging.error(f"PDF file not found at path: {doc_path}")
        return None


def split_documents(documents):
    """Split documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=850, chunk_overlap=300)
    chunks = text_splitter.split_documents(documents)
    logging.info("Documents split into chunks.")
    return chunks


def load_documents_metadata():
    """Load the documents metadata from JSON file."""
    if os.path.exists(DOCUMENTS_METADATA_FILE):
        try:
            with open(DOCUMENTS_METADATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in metadata file, starting fresh.")
            return {}
    return {}


def save_documents_metadata(metadata):
    """Save the documents metadata to JSON file."""
    os.makedirs(os.path.dirname(DOCUMENTS_METADATA_FILE), exist_ok=True)
    with open(DOCUMENTS_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def is_document_already_added(doc_path):
    """Check if a document has already been added to the vector store."""
    metadata = load_documents_metadata()
    return doc_path in metadata


def add_document_to_metadata(doc_path, title, chunks_count, authors="", acm_reference=""):
    """Add document information to metadata."""
    metadata = load_documents_metadata()
    metadata[doc_path] = {
        "title": title,
        "authors": authors,
        "acm_reference": acm_reference,
        "added_at": datetime.now().isoformat(),
        "chunks_count": chunks_count
    }
    save_documents_metadata(metadata)


def add_documents_to_vector_store(vector_db, documents):
    """Add new documents to an existing vector store."""
    if not documents:
        return vector_db
    
    chunks = split_documents(documents)
    vector_db.add_documents(chunks)
    vector_db.persist()
    
    # Update metadata
    for doc in documents:
        doc_path = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", os.path.basename(doc_path))
        authors = doc.metadata.get("authors", "")
        acm_reference = doc.metadata.get("acm_reference", "")
        chunks_count = len([c for c in chunks if c.metadata.get("source") == doc_path])
        add_document_to_metadata(doc_path, title, chunks_count, authors, acm_reference)
    
    logging.info(f"Added {len(chunks)} chunks from {len(documents)} documents to vector store.")
    return vector_db


def search_documents(search_term="", author_filter="", date_from="", date_to=""):
    """Search and filter documents based on various criteria."""
    metadata = load_documents_metadata()
    filtered_docs = {}
    
    for doc_path, info in metadata.items():
        # Text search in title, authors, and ACM reference
        if search_term:
            searchable_text = f"{info.get('title', '')} {info.get('authors', '')} {info.get('acm_reference', '')}".lower()
            if search_term.lower() not in searchable_text:
                continue
        
        # Author filter
        if author_filter and author_filter.lower() not in info.get('authors', '').lower():
            continue
        
        # Date range filter
        doc_date = info.get('added_at', '')[:10]  # Get YYYY-MM-DD part
        if date_from and doc_date < date_from:
            continue
        if date_to and doc_date > date_to:
            continue
        
        filtered_docs[doc_path] = info
    
    return filtered_docs


def update_document_metadata(doc_path, new_title, new_authors, new_acm_reference):
    """Update metadata for an existing document."""
    metadata = load_documents_metadata()
    if doc_path in metadata:
        metadata[doc_path]['title'] = new_title
        metadata[doc_path]['authors'] = new_authors
        metadata[doc_path]['acm_reference'] = new_acm_reference
        save_documents_metadata(metadata)
        return True
    return False


def delete_document_from_metadata(doc_path):
    """Remove document from metadata."""
    metadata = load_documents_metadata()
    if doc_path in metadata:
        del metadata[doc_path]
        save_documents_metadata(metadata)
        return True
    return False


def get_document_statistics():
    """Get statistics about the document collection."""
    metadata = load_documents_metadata()
    if not metadata:
        return {"total_docs": 0, "total_chunks": 0, "unique_authors": 0, "authors": [], "date_range": None}
    
    total_docs = len(metadata)
    total_chunks = sum(info.get('chunks_count', 0) for info in metadata.values())
    authors = set()
    dates = []
    
    for info in metadata.values():
        if info.get('authors'):
            # Split authors by comma and add to set
            doc_authors = [author.strip() for author in info['authors'].split(',')]
            authors.update(doc_authors)
        if info.get('added_at'):
            dates.append(info['added_at'][:10])
    
    date_range = (min(dates), max(dates)) if dates else None
    
    return {
        "total_docs": total_docs,
        "total_chunks": total_chunks,
        "unique_authors": len(authors),
        "authors": sorted(authors),
        "date_range": date_range
    }


@st.cache_resource
def load_vector_db():
    """Load or create the vector database."""
    # Pull the embedding model if not already available
    ollama.pull(EMBEDDING_MODEL)

    embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)

    if os.path.exists(PERSIST_DIRECTORY):
        vector_db = Chroma(
            embedding_function=embedding,
            collection_name=VECTOR_STORE_NAME,
            persist_directory=PERSIST_DIRECTORY,
        )
        logging.info("Loaded existing vector database.")
    else:
        # Load and process the initial PDF document
        data = ingest_pdf(DOC_PATH, "All about KAF")
        if data is None:
            return None

        # Split the documents into chunks
        chunks = split_documents(data)

        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding,
            collection_name=VECTOR_STORE_NAME,
            persist_directory=PERSIST_DIRECTORY,
        )
        vector_db.persist()
        
        # Initialize metadata
        add_document_to_metadata(DOC_PATH, "All about KAF", len(chunks))
        
        logging.info("Vector database created and persisted.")
    return vector_db


def get_vector_db_instance():
    """Get the vector database instance (non-cached for updates)."""
    ollama.pull(EMBEDDING_MODEL)
    embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    return Chroma(
        embedding_function=embedding,
        collection_name=VECTOR_STORE_NAME,
        persist_directory=PERSIST_DIRECTORY,
    )


def create_retriever(vector_db, llm):
    """Create a multi-query retriever."""
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to generate five
different versions of the given user question to retrieve relevant documents from
a vector database. By generating multiple perspectives on the user question, your
goal is to help the user overcome some of the limitations of the distance-based
similarity search. Provide these alternative questions separated by newlines.
Original question: {question}""",
    )

    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(), llm, prompt=QUERY_PROMPT
    )
    logging.info("Retriever created.")
    return retriever


def create_chain(retriever, llm):
    """Create the chain with preserved syntax."""
    # RAG prompt
    template = """Answer the question based ONLY on the following context:
{context} providing a detailed, considered response with citations from the context.
The audience is an expert accessibility auditor with may years of experience in software development, feel free to use appropriate terminology and ontologies.
If the question cannot be answered using the information provided, answer with "I don't know".
Question: {question}
"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("Chain created with preserved syntax.")
    return chain


def main():
    st.title("A11y Knowledge Base")
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["💬 Chat", "📚 Document Management"])
    
    with tab1:
        # Main chat interface
        user_input = st.text_input("Enter your question:", "")

        if user_input:
            with st.spinner("Generating response..."):
                try:
                    # Initialize the language model
                    llm = ChatOllama(model=MODEL_NAME, temperature=0.3, max_tokens=65536)

                    # Load the vector database
                    vector_db = load_vector_db()
                    if vector_db is None:
                        st.error("Failed to load or create the vector database.")
                        return

                    # Create the retriever
                    retriever = create_retriever(vector_db, llm)

                    # Create the chain
                    chain = create_chain(retriever, llm)

                    # Get the response
                    response = chain.invoke(input=user_input)

                    st.markdown("**Assistant:**")
                    st.write(response)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.info("Please enter a question to get started.")
    
    with tab2:
        st.header("Document Management")
        
        # Document statistics
        stats = get_document_statistics()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats["total_docs"])
        with col2:
            st.metric("Total Chunks", stats["total_chunks"])
        with col3:
            st.metric("Unique Authors", stats["unique_authors"])
        with col4:
            if stats["date_range"]:
                st.metric("Date Range", f"{stats['date_range'][0]} - {stats['date_range'][1]}")
            else:
                st.metric("Date Range", "N/A")
        
        st.divider()
        
        # Create sub-tabs for management functions
        mgmt_tab1, mgmt_tab2, mgmt_tab3 = st.tabs(["📋 Browse Documents", "➕ Add Document", "📊 Analytics"])
        
        with mgmt_tab1:
            st.subheader("Browse & Manage Documents")
            
            # Search and filter controls
            col1, col2 = st.columns(2)
            with col1:
                search_term = st.text_input("🔍 Search documents", placeholder="Search in title, authors, or reference...")
                author_filter = st.selectbox("👤 Filter by Author", [""] + stats["authors"])
            with col2:
                date_from = st.date_input("📅 From Date", value=None)
                date_to = st.date_input("📅 To Date", value=None)
            
            # Convert dates to string format if provided
            date_from_str = date_from.strftime("%Y-%m-%d") if date_from else ""
            date_to_str = date_to.strftime("%Y-%m-%d") if date_to else ""
            
            # Search documents
            filtered_docs = search_documents(search_term, author_filter, date_from_str, date_to_str)
            
            if filtered_docs:
                st.write(f"**Found {len(filtered_docs)} document(s)**")
                
                # Pagination
                docs_per_page = 10
                total_pages = (len(filtered_docs) + docs_per_page - 1) // docs_per_page
                
                if total_pages > 1:
                    page = st.selectbox("Page", range(1, total_pages + 1)) - 1
                else:
                    page = 0
                
                # Get documents for current page
                doc_items = list(filtered_docs.items())
                start_idx = page * docs_per_page
                end_idx = start_idx + docs_per_page
                page_docs = doc_items[start_idx:end_idx]
                
                # Display documents
                for doc_path, info in page_docs:
                    with st.expander(f"📄 {info['title']}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Display current metadata
                            st.write(f"**Title:** {info['title']}")
                            st.write(f"**Authors:** {info.get('authors', 'Not specified')}")
                            st.write(f"**ACM Reference:** {info.get('acm_reference', 'Not specified')}")
                            st.write(f"**Chunks:** {info['chunks_count']}")
                            st.write(f"**Added:** {info['added_at'][:10]}")
                            st.write(f"**Path:** {doc_path}")
                        
                        with col2:
                            # Edit button
                            if st.button(f"✏️ Edit", key=f"edit_{doc_path}"):
                                st.session_state[f"editing_{doc_path}"] = True
                            
                            # Delete button
                            if st.button(f"🗑️ Delete", key=f"delete_{doc_path}"):
                                if delete_document_from_metadata(doc_path):
                                    st.success("Document deleted from metadata!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete document.")
                        
                        # Edit form (appears when edit button is clicked)
                        if st.session_state.get(f"editing_{doc_path}", False):
                            st.divider()
                            st.write("**Edit Metadata:**")
                            
                            new_title = st.text_input("Title", value=info['title'], key=f"title_{doc_path}")
                            new_authors = st.text_input("Authors", value=info.get('authors', ''), key=f"authors_{doc_path}")
                            new_acm_ref = st.text_area("ACM Reference", value=info.get('acm_reference', ''), key=f"acm_{doc_path}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Save", key=f"save_{doc_path}"):
                                    if update_document_metadata(doc_path, new_title, new_authors, new_acm_ref):
                                        st.success("Metadata updated successfully!")
                                        st.session_state[f"editing_{doc_path}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to update metadata.")
                            
                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_{doc_path}"):
                                    st.session_state[f"editing_{doc_path}"] = False
                                    st.rerun()
            else:
                st.info("No documents found matching your criteria.")
        
        with mgmt_tab2:
            st.subheader("Add New Document")
            
            # File upload section
            uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
            document_title = st.text_input("Document Title (optional)", "")
            document_authors = st.text_input("Authors (optional)", placeholder="e.g., Smith, J., Doe, A.")
            acm_reference = st.text_area("ACM Bibliographic Reference (optional)", 
                                       placeholder="e.g., Smith, J. and Doe, A. 2023. Title of Paper. In Proceedings...")
            
            if uploaded_file is not None:
                if st.button("➕ Add Document"):
                    # Save uploaded file temporarily
                    temp_path = f"./temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        # Check if already added
                        if is_document_already_added(temp_path):
                            st.warning("This document has already been added.")
                        else:
                            # Process the document
                            title = document_title if document_title else uploaded_file.name
                            data = ingest_pdf(temp_path, title, document_authors, acm_reference)
                            
                            if data:
                                # Add to vector database
                                vector_db = get_vector_db_instance()
                                add_documents_to_vector_store(vector_db, data)
                                
                                # Clear cache to refresh the vector db
                                st.cache_resource.clear()
                                
                                st.success(f"Document '{title}' added successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to process the document.")
                    except Exception as e:
                        st.error(f"Error adding document: {str(e)}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
        
        with mgmt_tab3:
            st.subheader("Document Analytics")
            
            # Author distribution
            if stats["authors"]:
                st.write("**Author Distribution:**")
                metadata = load_documents_metadata()
                author_counts = {}
                for info in metadata.values():
                    if info.get('authors'):
                        doc_authors = [author.strip() for author in info['authors'].split(',')]
                        for author in doc_authors:
                            author_counts[author] = author_counts.get(author, 0) + 1
                
                # Sort by count
                sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
                for author, count in sorted_authors[:20]:  # Show top 20
                    st.write(f"- {author}: {count} document(s)")
            
            # Timeline
            st.write("**Documents Added Over Time:**")
            metadata = load_documents_metadata()
            date_counts = {}
            for info in metadata.values():
                date = info.get('added_at', '')[:10]
                if date:
                    date_counts[date] = date_counts.get(date, 0) + 1
            
            if date_counts:
                sorted_dates = sorted(date_counts.items())
                for date, count in sorted_dates:
                    st.write(f"- {date}: {count} document(s)")
            else:
                st.info("No date information available.")


if __name__ == "__main__":
    main()
