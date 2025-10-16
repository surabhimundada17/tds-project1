from fastapi import FastAPI, Request, BackgroundTasks
import os, json, base64
from dotenv import load_dotenv
from core_engine.intelligent_generator import create_dynamic_application, process_encoded_attachments
from core_engine.repository_manager import (
    initialize_project_repository,
    commit_project_file,
    activate_hosting_pages,
    generate_license_content,
)
from core_engine.evaluation_notifier import send_completion_notification
from core_engine.repository_manager import commit_binary_content

load_dotenv()
PRIVATE_ACCESS_KEY = os.getenv("USER_SECRET")
GITHUB_OWNER = os.getenv("GITHUB_USERNAME")
# Use /tmp for serverless environments like Vercel
TASK_CACHE_PATH = "/tmp/deployed_projects.json"

app = FastAPI(title="Smart Deploy Engine", description="AI-powered deployment system")

# === Task Cache Management System ===
def retrieve_completed_tasks():
    if os.path.exists(TASK_CACHE_PATH):
        try:
            return json.load(open(TASK_CACHE_PATH))
        except json.JSONDecodeError:
            return {}
    return {}

def store_completed_task(task_info):
    json.dump(task_info, open(TASK_CACHE_PATH, "w"), indent=2)

# === Project Deployment Processor ===
def execute_project_deployment(request_payload):
    current_iteration = request_payload.get("round", 1)
    project_identifier = request_payload["task"]
    print(f"⚡ Initiating deployment for project {project_identifier} (iteration {current_iteration})")

    project_assets = request_payload.get("attachments", [])
    processed_assets = process_encoded_attachments(project_assets)
    print("Assets processed:", processed_assets)

    # Retrieve previous documentation for iteration 2+
    existing_documentation = None
    if current_iteration == 2:
        try:
            target_repo = initialize_project_repository(project_identifier, f"Enhanced solution: {request_payload['brief']}")
            doc_file = target_repo.get_contents("README.md")
            existing_documentation = doc_file.decoded_content.decode("utf-8", errors="ignore")
            print("📄 Retrieved existing documentation for enhancement.")
        except Exception:
            existing_documentation = None

    code_generation_result = create_dynamic_application(
        request_payload["brief"],
        attachments=project_assets,
        validation_criteria=request_payload.get("checks", []),
        iteration_number=current_iteration,
        existing_docs=existing_documentation
        )

    application_files = code_generation_result.get("files", {})
    asset_metadata = code_generation_result.get("attachments", [])

    # Step 1: Repository initialization
    target_repo = initialize_project_repository(project_identifier, description=f"Auto-deployed solution: {request_payload['brief']}")

    # Step 2: Iteration-specific deployment strategy
    if current_iteration == 1:
        print("🚀 Initial deployment: Setting up fresh repository...")
        # Deploy all assets to repository
        for asset in asset_metadata:
            asset_path = asset["name"]
            try:
                with open(asset["path"], "rb") as f:
                    asset_bytes = f.read()
                if asset["mime"].startswith("text") or asset["name"].endswith((".md", ".csv", ".json", ".txt")):
                    text_data = asset_bytes.decode("utf-8", errors="ignore")
                    commit_project_file(target_repo, asset_path, text_data, f"Deploy asset {asset_path}")
                else:
                    commit_binary_content(target_repo, asset_path, asset_bytes, f"Deploy binary {asset_path}")
                    # Create backup
                    encoded_backup = base64.b64encode(asset_bytes).decode("utf-8")
                    commit_project_file(target_repo, f"assets/{asset['name']}.encoded", encoded_backup, f"Backup {asset['name']}")
            except Exception as e:
                print("⚠️ Asset deployment failed:", e)
    else:
        print("🔄 Enhancement deployment: Updating existing repository...")
        # Update files for subsequent iterations
        for file_name, file_data in application_files.items():
            commit_project_file(target_repo, file_name, file_data, f"Enhance {file_name} - iteration {current_iteration}")

    # Step 3: Deploy all generated application files
    for file_name, file_data in application_files.items():
        commit_project_file(target_repo, file_name, file_data, f"Deploy {file_name}")

    # Step 4: Add license
    license_content = generate_license_content()
    commit_project_file(target_repo, "LICENSE", license_content, "Add MIT license")

    # Step 5: Configure hosting
    if request_payload["round"] == 1:
        hosting_activated = activate_hosting_pages(project_identifier)
        hosting_url = f"https://{GITHUB_OWNER}.github.io/{project_identifier}/" if hosting_activated else None
    else:
        # Hosting already configured
        hosting_activated = True
        hosting_url = f"https://{GITHUB_OWNER}.github.io/{project_identifier}/"

    # Get latest commit information
    try:
        latest_commit = target_repo.get_commits()[0].sha
    except Exception:
        latest_commit = None

    # Prepare notification data
    nonce_value = request_payload.get("nonce", "default-nonce")
    notification_data = {
        "email": request_payload["email"],
        "task": request_payload["task"],
        "round": current_iteration,
        "nonce": nonce_value,
        "repo_url": target_repo.html_url,
        "commit_sha": latest_commit,
        "pages_url": hosting_url,
    }

    # Send completion notification
    evaluation_url = request_payload.get("evaluation_url")
    if evaluation_url:
        send_completion_notification(evaluation_url, notification_data)

    # Update task cache
    completed_tasks = retrieve_completed_tasks()
    cache_identifier = f"{request_payload['email']}::{request_payload['task']}::round{current_iteration}::nonce{nonce_value}"
    completed_tasks[cache_identifier] = notification_data
    store_completed_task(completed_tasks)

    print(f"✅ Deployment completed for iteration {current_iteration} of {project_identifier}")
    
    # Print the GitHub Pages URL prominently
    if hosting_url:
        print("🌐" + "="*60)
        print(f"🚀 LIVE WEBSITE: {hosting_url}")
        print(f"📁 REPOSITORY: {target_repo.html_url}")
        print("🌐" + "="*60)
    else:
        print("⚠️ GitHub Pages URL not available yet. It may take a few minutes to deploy.")
        print(f"📁 REPOSITORY: {target_repo.html_url}")


# === Main API Endpoint ===
@app.post("/deploy-endpoint")
async def handle_deployment_request(request: Request, background_tasks: BackgroundTasks):
    request_data = await request.json()
    print("📨 Deployment request received:", request_data)

    # Step 0: Authentication
    if request_data.get("secret") != PRIVATE_ACCESS_KEY:
        print("❌ Authentication failed.")
        return {"error": "Invalid authentication credentials"}

    completed_tasks = retrieve_completed_tasks()
    
    # Handle missing required fields gracefully
    required_fields = ['email', 'task', 'round']
    for field in required_fields:
        if field not in request_data:
            return {"error": f"Missing required field: {field}"}
    
    # Use nonce if provided, otherwise generate a simple identifier
    nonce_value = request_data.get('nonce', 'default-nonce')
    task_key = f"{request_data['email']}::{request_data['task']}::round{request_data['round']}::nonce{nonce_value}"

    # Handle duplicate requests
    if task_key in completed_tasks:
        print(f"⚠️ Duplicate request detected for {task_key}. Re-sending notification.")
        cached_result = completed_tasks[task_key]
        evaluation_url = request_data.get("evaluation_url")
        if evaluation_url:
            send_completion_notification(evaluation_url, cached_result)
        
        # Print URLs for duplicate requests too
        task_id = request_data["task"]
        expected_pages_url = f"https://{GITHUB_OWNER}.github.io/{task_id}/"
        expected_repo_url = f"https://github.com/{GITHUB_OWNER}/{task_id}"
        
        print("🌐" + "="*60)
        print(f"🚀 EXISTING WEBSITE: {expected_pages_url}")
        print(f"📁 EXISTING REPO:    {expected_repo_url}")
        print("🌐" + "="*60)
        print("💡 Your website is already deployed and ready to view!")
        
        return {
            "status": "success", 
            "note": "duplicate request handled and re-notified",
            "pages_url": expected_pages_url,
            "repo_url": expected_repo_url,
            "cached_result": cached_result
        }

    # Queue deployment task
    background_tasks.add_task(execute_project_deployment, request_data)

    # Return immediate response
    response_data = {
        "status": "processing", 
        "note": f"deployment initiated for round {request_data['round']}",
        "task_id": request_data["task"],
        "expected_pages_url": f"https://{GITHUB_OWNER}.github.io/{request_data['task']}/",
        "expected_repo_url": f"https://github.com/{GITHUB_OWNER}/{request_data['task']}"
    }
    
    print(f"📋 Expected URLs:")
    print(f"   🌐 Pages: {response_data['expected_pages_url']}")
    print(f"   📁 Repo:  {response_data['expected_repo_url']}")
    
    return response_data

# === Health Check ===
@app.get("/health")
async def system_health():
    return {"status": "operational", "version": "1.2.0"}