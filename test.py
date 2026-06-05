from pathlib import Path
from dotenv import load_dotenv
from src import OpenAIEmbedder

load_dotenv(dotenv_path=Path(".env"), override=False)
embedder = OpenAIEmbedder()
print(embedder._backend_name, len(embedder("embedding smoke test")))