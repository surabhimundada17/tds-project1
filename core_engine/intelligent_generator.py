import os
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import httpx

load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_BASE_URL = "https://aipipe.org/openai/v1"

ATTACHMENT_STORAGE = Path("/tmp/project_attachments")
ATTACHMENT_STORAGE.mkdir(parents=True, exist_ok=True)

def process_encoded_attachments(attachment_list):
    """
    attachment_list: list of {name, url: data:<mime>;base64,<content>}
    Saves files to /tmp/project_attachments/<name>
    Returns list of metadata: {"name": name, "path": "/tmp/..", "mime": mime, "size": n}
    """
    processed_attachments = []
    for attachment in attachment_list or []:
        attachment_name = attachment.get("name") or "untitled_attachment"
        data_url = attachment.get("url", "")
        if not data_url.startswith("data:"):
            continue
        try:
            url_header, encoded_content = data_url.split(",", 1)
            content_type = url_header.split(";")[0].replace("data:", "")
            decoded_data = base64.b64decode(encoded_content)
            storage_path = ATTACHMENT_STORAGE / attachment_name
            with open(storage_path, "wb") as f:
                f.write(decoded_data)
            processed_attachments.append({
                "name": attachment_name,
                "path": str(storage_path),
                "mime": content_type,
                "size": len(decoded_data)
            })
        except Exception as e:
            print("Failed to process attachment", attachment_name, e)
    return processed_attachments

def generate_attachment_summary(processed_list):
    """
    processed_list is from process_encoded_attachments.
    Returns a concise summary for AI prompt context.
    """
    attachment_summaries = []
    for item in processed_list:
        name = item["name"]
        path = item["path"]
        mime_type = item.get("mime", "")
        try:
            if mime_type.startswith("text") or name.endswith((".md", ".txt", ".json", ".csv")):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    if name.endswith(".csv"):
                        sample_lines = [next(f).strip() for _ in range(3)]
                        content_preview = "\\n".join(sample_lines)
                    else:
                        content_data = f.read(800)
                        content_preview = content_data.replace("\n", "\\n")[:800]
                attachment_summaries.append(f"- {name} ({mime_type}): {content_preview}")
            else:
                attachment_summaries.append(f"- {name} ({mime_type}): {item['size']} bytes")
        except Exception as e:
            attachment_summaries.append(f"- {name} ({mime_type}): (preview unavailable: {e})")
    return "\\n".join(attachment_summaries)

def extract_code_content(ai_response: str) -> str:
    """
    Extract code from AI response, removing markdown code blocks if present.
    """
    if "```" in ai_response:
        code_blocks = ai_response.split("```")
        if len(code_blocks) >= 2:
            return code_blocks[1].strip()
    return ai_response.strip()

def generate_fallback_documentation(project_brief: str, validation_checks=None, attachment_summary=None, iteration=1):
    check_list = "\\n".join(validation_checks or [])
    attachment_info = attachment_summary or ""
    return f"""# Project Documentation (Iteration {iteration})

**Project Brief:** {project_brief}

**Available Attachments:**
{attachment_info}

**Validation Requirements:**
{check_list}

## Installation
1. Open `index.html` in a web browser.
2. No additional setup required.

## Usage
This application was auto-generated based on the provided specifications.

## Notes
Generated as fallback when AI service was unavailable.
"""

def create_dynamic_application(project_brief: str, attachments=None, validation_criteria=None, iteration_number=1, existing_docs=None):
    """
    Generate or enhance an application using AI.
    - iteration_number=1: create from scratch
    - iteration_number=2+: enhance based on new requirements and existing documentation
    """
    processed_assets = process_encoded_attachments(attachments or [])
    attachment_summary = generate_attachment_summary(processed_assets)

    enhancement_context = ""
    if iteration_number == 2 and existing_docs:
        enhancement_context = f"\\n### Existing Documentation:\\n{existing_docs}\\n\\nEnhance this project based on the new requirements below.\\n"

    ai_prompt = f"""
You are an expert web application developer.

### Iteration Number
{iteration_number}

### Project Requirements
{project_brief}

{enhancement_context}

### Available Assets
{attachment_summary}

### Validation Criteria
{validation_criteria or []}

### Response Format Requirements:
1. Create a complete, functional web application that meets all requirements.
2. Provide exactly TWO sections:
   - Complete HTML application code (with inline CSS/JS if needed)
   - Project documentation (starts after the delimiter: ---DOCUMENTATION---)
3. Documentation must include:
   - Project overview
   - Setup instructions
   - Usage guide
   - If iteration 2+, explain enhancements from previous version.
4. No additional commentary outside code or documentation.
"""

    try:
        # Use AIPipe responses endpoint
        headers = {
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Format input for AIPipe responses API
        input_messages = [
            {"role": "system", "content": "You are an expert web developer that creates complete, functional applications."},
            {"role": "user", "content": ai_prompt}
        ]
        
        payload = {
            "model": "gpt-4.1-nano",
            "input": input_messages
        }
        
        response = httpx.post(
            f"{AIPIPE_BASE_URL}/responses",
            headers=headers,
            json=payload,
            timeout=60.0
        )
        
        if response.status_code == 200:
            response_data = response.json()
            # Extract content from AIPipe response format
            output = response_data.get("output", [])
            if output and len(output) > 0:
                content_items = output[0].get("content", [])
                if content_items and len(content_items) > 0:
                    response_content = content_items[0].get("text", "")
                else:
                    response_content = ""
            else:
                response_content = ""
            print("✅ AI application generated successfully using AIPipe.")
        else:
            print(f"⚠️ AIPipe API failed with status {response.status_code}: {response.text}")
            raise Exception(f"AIPipe API error: {response.status_code}")
            
    except Exception as e:
        print("⚠️ AIPipe API unavailable, using fallback:", e)
        response_content = f"""
<html>
  <head><title>Generated Application</title></head>
  <body>
    <h1>Auto-Generated Application</h1>
    <p>This application was created as a fallback. Requirements: {project_brief}</p>
  </body>
</html>

---DOCUMENTATION---
{generate_fallback_documentation(project_brief, validation_criteria, attachment_summary, iteration_number)}
"""

    if "---DOCUMENTATION---" in response_content:
        application_code, documentation = response_content.split("---DOCUMENTATION---", 1)
        application_code = extract_code_content(application_code)
        documentation = extract_code_content(documentation)
    else:
        application_code = extract_code_content(response_content)
        documentation = generate_fallback_documentation(project_brief, validation_criteria, attachment_summary, iteration_number)

    output_files = {"index.html": application_code, "README.md": documentation}
    return {"files": output_files, "attachments": processed_assets}