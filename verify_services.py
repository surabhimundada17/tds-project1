from github import Github, Auth
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# -------------------------
# GitHub Integration Test
# -------------------------
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ACCOUNT = os.getenv("GITHUB_USERNAME")

auth_handler = Auth.Token(GITHUB_ACCESS_TOKEN)
github_client = Github(auth=auth_handler)

# Verify GitHub authentication
authenticated_user = github_client.get_user()
print(f"🔐 GitHub Authentication Success: {authenticated_user.login}")

if authenticated_user.login != GITHUB_ACCOUNT:
    print(f"⚠️ Warning: Environment username ({GITHUB_ACCOUNT}) doesn't match authenticated user ({authenticated_user.login})")

print("\\n📂 Repository listing (first 5):")
for repository in authenticated_user.get_repos()[:5]:
    print("-", repository.name)

# -------------------------
# AIPipe Service Test
# -------------------------
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")

try:
    headers = {"Authorization": f"Bearer {AIPIPE_TOKEN}"}
    response = httpx.get("https://aipipe.org/openai/v1/models", headers=headers, timeout=30.0)
    
    if response.status_code == 200:
        models_data = response.json()
        print("\\n✅ AIPipe Service Connected. Available models:")
        for model in models_data.get("data", [])[:5]:
            print("-", model.get("id", "unknown"))
    else:
        print(f"\\n❌ AIPipe Service Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print("\\n❌ AIPipe Service Error:", e)

print("\\n🚀 All services verified successfully!")