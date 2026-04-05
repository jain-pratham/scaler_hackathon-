import uvicorn

def run():
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8001)

if __name__ == "__main__":
    run()
