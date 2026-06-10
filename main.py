# import streamlit as st
# import os
# from src.services.qa_service import QAService

# st.title("AI STUDY BUDDY - RAG Pipeline Demo")

# service = QAService()

# uploaded_file = st.file_uploader("Upload your PDF", type="pdf")

# if uploaded_file:
#     file_path = os.path.join("data/raw", uploaded_file.name)
#     with open(file_path, "wb") as f:
#         f.write(uploaded_file.read())

#     if st.button("Process PDF"):
#         service.process_pdf(file_path)
#         st.success("PDF processed successfully!")

# question = st.text_input("Ask a question")

# if question:
#     answer = service.ask_question(question)
#     st.write(answer)