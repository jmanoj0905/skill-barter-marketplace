from fastapi import FastAPI

app = FastAPI()

@app.post("/session/{barter_id}/contract")
def contract(barter_id: int):
    print(f"📄 Contract service called for barter {barter_id}")
    return {"status": "contract created"}

@app.post("/session/{barter_id}/init")
def init(barter_id: int):
    print(f"📡 Monitoring started for barter {barter_id}")
    return {"status": "monitoring started"}

@app.post("/session/{barter_id}/end")
def end(barter_id: int):
    print(f"✅ Session completed for barter {barter_id}")
    return {"status": "completed"}