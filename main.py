import uvicorn
from app.main import app

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    print("🦁 Starting Safari AI Pro...")
    uvicorn.run(app, host="0.0.0.0", port=port)
