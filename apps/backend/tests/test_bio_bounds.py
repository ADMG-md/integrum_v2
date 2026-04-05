import asyncio
import httpx
import json

async def test_bio_bounds():
    url = "http://localhost:8000/api/v1/encounter/process"
    headers = {"Content-Type": "application/json"}
    
    # 1. Test out of bounds (should fail)
    bad_payload = {
        "patient_id": "TEST-FLOW-001",
        "observations": [
            {"code": "2339-0", "value": 9999, "unit": "mg/dL"} # Glucose too high
        ]
    }
    
    async with httpx.AsyncClient() as client:
        # We need a token, but for a quick internal check we might just look at the validation logic
        print("Testing bio-boundary rejection...")
        # Since I am an agent, I can't easily get a real JWT without login flow, 
        # but I can check if the server is running and try a request.
        try:
            res = await client.post(url, json=bad_payload)
            if res.status_code == 422:
                print("SUCCESS: Data rejected as expected (422 Unprocessable Entity)")
                print(f"Error detail: {res.json()['detail'][0]['msg']}")
            else:
                print(f"FAILURE: Expected 422, got {res.status_code}")
        except Exception as e:
            print(f"Server connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bio_bounds())
