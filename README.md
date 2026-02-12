# Scientific Library Search

**Table of Contents**

- [License](#license)
- [Changelog](#changelog)
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage (Docker)](#usage-docker)
  - [Build the image](#build-the-image)
  - [Run the Indexer (All)](#run-the-indexer-all)
  - [Run the Server](#run-the-server)
  - [Dry Run](#dry-run)
  - [Clean](#clean)
- [Usage (non-Docker)](#usage-non-docker)
  - [Indexing Your Library](#indexing-your-library)
  - [Running the Server](#running-the-server)

## License
[Distributed under the GPL License. See `LICENSE` for more information.](LICENSE)


## Changelog

- **2026-02-12**:
    - Augmented indexing strategy with content-based parsing (TOC, Abstract, and Introduction).
    - Added OCR fallback using Tesseract for scanned PDF documents (first 25 pages).
    - Integrated DJVU text extraction support via `djvutxt`.
    - Enhanced file discovery to support numerical suffixes (e.g., `.pdf.1`).
    - Combined glossary matching with NLTK-based noun-phrase extraction for more thorough technical token discovery.
- **2026-02-10**: 
    - Added favicon to the search frontend and configured `app.py` to serve it.
    - Added Docker commands for `all`, `dryrun`, and `clean` to the documentation.
- **2026-02-09**: 
    - Standardized all document paths to be relative to the project root.
    - Updated `library_indexer.py` and `incremental_indexer.py` to use `os.path.relpath` for metadata, caching, and database storage.
- **2026-02-05**: 
    - Updated search frontend header to "Personal library search".
- **2026-02-04**: 
    - Enhanced filename parsing to robustly extract publication years (1700-2099) and editions (e.g., "2nd Ed") from filenames.
    - Updated Search UI to support filtering by year (`year:1948`) and displaying edition information.
    - Cleaned up source indicator files and reorganized auxiliary maintenance scripts.
- **2026-01-27**: 
    - Initial release.
    - Implemented Wikipedia-enhanced indexing: tokenizes filenames and expands technical terms using Wikipedia summaries.
    - Added incremental indexing with caching and parallel processing support.
    - Added Docker support for easy deployment (optimized for Raspberry Pi 4).

## Introduction

**Scientific Library Search** is a lightweight, self-hosted search engine designed for personal document collections. Unlike traditional full-text search engines that require resource-intensive OCR, this project leverages smart filename parsing and **Wikipedia expansion**.

It extracts metadata (Author, Title, Year, Edition) from filenames and identifies technical terms using a local glossary. Furthermore, it now parses the **document content** (TOC, Abstracts) and employs **OCR fallback** for scanned documents. It can also query Wikipedia for identified terms to fetch related keywords, creating a rich search index. This hybrid approach ensures high speed while providing thorough discoverability even for documents without text layers.

Supported formats: PDF, DJVU, EPUB, MOBI.

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage (Docker)

You can run the entire stack using Docker, which is recommended for deployment (e.g., on a Raspberry Pi).

1.  **Build the image:**
    ```bash
    docker build -t library-search .
    ```

2.  **Run the Indexer (All):**
    Mount your current directory (`$(pwd)`) to `/app` so the container can see your files and write the `library.json` back to your host.
    ```bash
    docker run -v $(pwd):/app library-search index --cores 4
    ```

3.  **Run the Full Indexer (with Wikipedia):**
    ```bash
    docker run -v $(pwd):/app library-search full-index
    ```

4.  **Run the Server:**
    ```bash
    docker run -p 5000:5000 -v $(pwd):/app library-search server
    ```
    The UI will be available at `http://localhost:5000`.

5.  **Dry Run:**
    Simulate the indexing process without writing any changes:
    ```bash
    docker run -v $(pwd):/app library-search dryrun
    ```

6.  **Clean:**
    Remove the metadata cache and the generated library database:
    ```bash
    docker run -v $(pwd):/app library-search clean
    ```

## Usage (non-Docker)

### Indexing Your Library

To build the search index (`library.json`), run:

```bash
make index
```

This will scan the current directory (and subdirectories) for supported files.
- Use `--cores N` to run in parallel (e.g., `python3 incremental_indexer.py --cores 4`).
- Use `--full` to enable Wikipedia expansion (requires internet connection).

### Running the Server

Start the web interface:

```bash
make server
```

The UI will be available at `http://localhost:5000`.
