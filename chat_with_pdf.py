# API_KEY=sk-c8xPiNSZUXUhLNS_DJ3w4w streamlit run chat_with_pdf.py 
import streamlit as st
import os
from openai import OpenAI
from os import environ
from PyPDF2 import PdfReader  # Import PyPDF2 for PDF handling
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import tempfile
import shutil

os.environ["OPENAI_API_KEY"] = os.environ["API_KEY"]

client = OpenAI(
    api_key=os.environ["API_KEY"],
    base_url="https://api.ai.it.cornell.edu",
)

# Function to process file content based on file type
def process_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)  # Read PDF files
        extracted_text = ""
        for page in pdf_reader.pages:
            page_content = page.extract_text()
            if page_content:
                extracted_text += page_content + "\n"  # Extract text from each page
        return extracted_text
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")  # Read and decode text files
    return ""

# Function to chunk text using RecursiveCharacterTextSplitter
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

# Function to format documents for display
def format_docs(docs):
    return "\n\n---\n\n".join(d.page_content for d in docs)

# Function to build vector store from current documents
def build_vectorstore(documents_state):
    all_chunks_with_metadata = []
    
    for doc_name, chunks in documents_state.items():
        # Create Document objects with metadata for Chroma
        for chunk in chunks:
            all_chunks_with_metadata.append(
                Document(
                    page_content=chunk,
                    metadata={"source": doc_name}
                )
            )
    
    if all_chunks_with_metadata:
        try:
            # Use in-memory ChromaDB to avoid file permission issues
            vectorstore = Chroma.from_documents(
                documents=all_chunks_with_metadata, 
                embedding=OpenAIEmbeddings(
                    model="openai.text-embedding-3-large",
                    openai_api_key=os.environ["API_KEY"],
                    openai_api_base="https://api.ai.it.cornell.edu"
                ),
                persist_directory=None  # In-memory only
            )
            return vectorstore
        except Exception as e:
            st.error(f"Error creating vector store: {e}")
            return None
    return None

st.title("📝 Multi-Document Q&A with OpenAI")

# Initialize ALL session state variables at the top
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Ask something about the uploaded articles"}]

if "documents" not in st.session_state:
    st.session_state["documents"] = {}  # Store content of all uploaded documents

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # Preserve chat history across interactions

if "vectorstore" not in st.session_state:
    st.session_state["vectorstore"] = None  # Store the Chroma vector store

if "current_uploaded_files" not in st.session_state:
    st.session_state["current_uploaded_files"] = set()  # Track currently uploaded files

if "clear_triggered" not in st.session_state:
    st.session_state["clear_triggered"] = False  # Track if clear was triggered

# Clear functionality - must be before file uploader
if st.session_state["clear_triggered"]:
    # Reset everything
    st.session_state["documents"] = {}
    st.session_state["current_uploaded_files"] = set()
    st.session_state["vectorstore"] = None
    st.session_state["messages"] = [{"role": "assistant", "content": "Ask something about the uploaded articles"}]
    st.session_state["clear_triggered"] = False
    # Use experimental_rerun to clear the file uploader
    st.rerun()

# File uploader - now it will be cleared when clear is triggered
uploaded_files = st.file_uploader("Upload articles (multiple allowed)", type=("txt", "pdf"), accept_multiple_files=True, key="file_uploader")  # Added key for better control

question = st.chat_input(
    "Ask something about the uploaded articles",
    disabled=not uploaded_files,
)

# Track file changes and update vector store accordingly
if uploaded_files is not None:
    current_files = {file.name for file in uploaded_files}
    previous_files = st.session_state["current_uploaded_files"]
    
    # Check for changes in uploaded files
    files_added = current_files - previous_files
    files_removed = previous_files - current_files
    needs_update = False
    
    # Process newly added files
    if files_added:
        for uploaded_file in uploaded_files:
            if uploaded_file.name in files_added and uploaded_file.name not in st.session_state["documents"]:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    file_content = process_uploaded_file(uploaded_file)
                    if file_content.strip():  # Only process if we got content
                        chunks = chunk_text(file_content)  # Chunk the text
                        st.session_state["documents"][uploaded_file.name] = chunks
                        needs_update = True
                        st.success(f"Processed: {uploaded_file.name} ({len(chunks)} chunks)")
                    else:
                        st.warning(f"No text content found in: {uploaded_file.name}")
    
    # Remove deleted files
    if files_removed:
        for removed_file in files_removed:
            if removed_file in st.session_state["documents"]:
                del st.session_state["documents"][removed_file]
                st.info(f"Removed: {removed_file}")
                needs_update = True
    
    # Update current uploaded files tracking
    st.session_state["current_uploaded_files"] = current_files
    
    # Rebuild vector store if there were changes
    if needs_update:
        if st.session_state["documents"]:
            with st.spinner("Updating search index..."):
                st.session_state["vectorstore"] = build_vectorstore(st.session_state["documents"])
                if st.session_state["vectorstore"]:
                    st.success("Search index updated successfully!")
        else:
            st.session_state["vectorstore"] = None
            st.info("All documents have been removed.")

# Show current document status
with st.expander("📁 Current Documents", expanded=False):
    if st.session_state["documents"]:
        st.write(f"**Loaded {len(st.session_state['documents'])} document(s):**")
        for doc_name, chunks in st.session_state["documents"].items():
            st.write(f"• {doc_name} ({len(chunks)} chunks)")
        
        # Show files that are uploaded but not in documents (empty files)
        uploaded_file_names = {file.name for file in uploaded_files} if uploaded_files else set()
        document_file_names = set(st.session_state["documents"].keys())
        empty_files = uploaded_file_names - document_file_names
        if empty_files:
            st.write("**Files with no text content:**")
            for empty_file in empty_files:
                st.write(f"• {empty_file} (no text found)")
    else:
        st.write("No documents processed yet")

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if question and uploaded_files and st.session_state["vectorstore"]:
    # Use vector store for semantic search across ALL documents
    k = 5  # Number of relevant chunks to retrieve
    
    try:
        # 1) Retrieve relevant chunks using semantic search from ALL documents
        docs = st.session_state["vectorstore"].similarity_search(question, k=k)
        
        # 2) Build a concise instruction with the retrieved context
        context = format_docs(docs)
        system_instructions = (
            "You are a helpful assistant for question answering.\n"
            "Use ONLY the provided context to answer the question concisely.\n"
            "If the answer isn't in the context, say you don't know.\n\n"
            f"Context:\n{context}"
        )

        # Append the user's question to the messages
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        with st.chat_message("assistant"):
            # 3) Ask the model with retrieved context from ALL documents
            stream = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=[
                    {"role": "system", "content": system_instructions},
                    *st.session_state.messages
                ],
                stream=True
            )
            
            response_content = ""
            response_container = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response_content += chunk.choices[0].delta.content
                    response_container.write(response_content)
            
            response = response_content

        # Append the assistant's response to the messages
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        # 4) Display sources from ALL relevant documents
        with st.expander("🔍 View Sources", expanded=False):
            st.write("**Relevant sources used for this answer:**")
            source_counts = {}
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "(no source)")
                if source not in source_counts:
                    source_counts[source] = 0
                source_counts[source] += 1
                
            st.write("**Documents referenced:**")
            for source, count in source_counts.items():
                st.write(f"• {source} ({count} chunk{'s' if count > 1 else ''})")
            
            st.write("---")
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "(no source)")
                st.write(f"**Source {i} - {source}:**")
                st.text_area(f"Content from source {i}", doc.page_content, height=100, key=f"source_{i}_{question}")
    
    except Exception as e:
        st.error(f"Error during search or response generation: {e}")

elif question and uploaded_files and not st.session_state["vectorstore"]:
    st.error("Search index not ready. Please wait for document processing to complete or upload valid documents.")

# Add a button to clear all documents and start fresh - placed at the end
if st.session_state["documents"] or (uploaded_files and len(uploaded_files) > 0):
    if st.button("🔄 Clear All Documents and Start Over"):
        st.session_state["clear_triggered"] = True
        st.rerun()