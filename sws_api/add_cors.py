from pathlib import Path

path = Path("main.py")
text = path.read_text()

text = text.replace(
    "from fastapi import FastAPI\n",
    "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n"
)

text = text.replace(
    "app = FastAPI(lifespan=lifespan)\n",
    """app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
)

path.write_text(text)
