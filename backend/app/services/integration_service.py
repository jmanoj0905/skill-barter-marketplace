import requests

# 🔹 Person 3 - Contract Service
def notify_contract_service(barter_id: int):
    try:
        response = requests.post(
            f"http://localhost:8002/session/{barter_id}/contract",
            json={"barter_id": barter_id},
            timeout=5
        )
        print("✅ Contract Service:", response.status_code)
    except Exception as e:
        print("❌ Contract Service Failed:", str(e))


# 🔹 Person 4 - Monitoring Service
def notify_monitoring_service(barter_id: int):
    try:
        response = requests.post(
            f"http://localhost:8003/session/{barter_id}/init",
            json={"barter_id": barter_id},
            timeout=5
        )
        print("✅ Monitoring Service:", response.status_code)
    except Exception as e:
        print("❌ Monitoring Service Failed:", str(e))


# 🔹 Person 2 - Completion Service
def notify_completion_service(barter_id: int):
    try:
        response = requests.post(
            f"http://localhost:8001/session/{barter_id}/end",
            json={"barter_id": barter_id},
            timeout=5
        )
        print("✅ Completion Service:", response.status_code)
    except Exception as e:
        print("❌ Completion Service Failed:", str(e))