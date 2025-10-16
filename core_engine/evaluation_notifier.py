# core_engine/evaluation_notifier.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def send_completion_notification(notification_endpoint: str, result_payload: dict) -> bool:
    """
    Send project completion details to the evaluation endpoint.
    Implements retry logic with exponential backoff.
    """
    # Skip notification if endpoint is None or empty
    if not notification_endpoint:
        print("⚠️ No evaluation endpoint provided, skipping notification.")
        return True
    
    request_headers = {"Content-Type": "application/json"}

    retry_delay = 1  # Initial delay in seconds
    max_attempts = 5
    
    for attempt_number in range(max_attempts):
        try:
            response = httpx.post(notification_endpoint, headers=request_headers, json=result_payload)
            if response.status_code == 200:
                print("✅ Evaluation endpoint notified successfully.")
                return True
            else:
                print(f"⚠️ Attempt {attempt_number+1}: Endpoint responded with {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Attempt {attempt_number+1} failed: {e}")

        # Apply exponential backoff
        import time
        time.sleep(retry_delay)
        retry_delay *= 2

    print("❌ Failed to notify evaluation endpoint after all retry attempts.")
    return False