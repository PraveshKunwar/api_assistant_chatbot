FROM registry.access.redhat.com/ubi8/python-39

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app.py .
COPY umich.png .
COPY API_Directory_logo_draft.png .
COPY API_DIRectory_mobile_logo_draft.png .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]