FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any (e.g. for pdfplumber dependencies if wheels are missing on ARM)
# but python-slim usually has what is needed for pure python wheels. 
# Explicitly ensuring git or other tools aren't needed unless specified.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python3 -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng')"

COPY . .

# Copy the entrypoint script and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["help"]
