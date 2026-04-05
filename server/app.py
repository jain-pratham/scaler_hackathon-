from backend.app.main import app

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
