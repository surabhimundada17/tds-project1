# core_engine/repository_manager.py
import os
from github import Github
from github import GithubException
import httpx
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
REPOSITORY_OWNER = os.getenv("GITHUB_USERNAME")
github_client = Github(GITHUB_ACCESS_TOKEN)

def initialize_project_repository(repo_identifier: str, description: str = ""):
    """
    Create a public repository with the specified identifier.
    """
    user_account = github_client.get_user()
    # Check if repository already exists
    try:
        existing_repo = user_account.get_repo(repo_identifier)
        print("Repository already exists:", existing_repo.full_name)
        return existing_repo
    except GithubException:
        pass

    new_repo = user_account.create_repo(
        name=repo_identifier,
        description=description,
        private=False,
        auto_init=False
    )
    print("Repository created:", new_repo.full_name)
    return new_repo

def commit_project_file(repository, file_path: str, file_content: str, commit_message: str):
    """
    Create a new file or update existing file in repository.
    """
    try:
        # Check if file exists
        existing_file = repository.get_contents(file_path)
        file_sha = existing_file.sha
        repository.update_file(file_path, commit_message, file_content, file_sha)
        print(f"Updated {file_path} in {repository.full_name}")
    except GithubException as e:
        # File doesn't exist, create new
        if e.status == 404:
            repository.create_file(file_path, commit_message, file_content)
            print(f"Created {file_path} in {repository.full_name}")
        else:
            # Other error
            raise


def commit_binary_content(repository, file_path: str, binary_data, commit_message: str):
    """
    Create or update a binary file in the repository.
    """
    try:
        # Check if file exists
        try:
            existing_file = repository.get_contents(file_path)
            # Update existing binary file
            repository.update_file(
                path=file_path,
                message=commit_message,
                content=binary_data,
                sha=existing_file.sha
            )
            print(f"Updated binary file {file_path} in {repository.full_name}")
        except GithubException as e:
            # File doesn't exist, create it
            if e.status == 404:
                repository.create_file(
                    path=file_path,
                    message=commit_message,
                    content=binary_data
                )
                print(f"Created binary file {file_path} in {repository.full_name}")
            else:
                # Other error
                raise
        return True
    except Exception as e:
        print(f"Error managing binary file {file_path}: {e}")
        return False

def activate_hosting_pages(repo_identifier: str, source_branch: str = "main"):
    """
    Enable GitHub Pages hosting via REST API.
    """
    api_endpoint = f"https://api.github.com/repos/{REPOSITORY_OWNER}/{repo_identifier}/pages"
    request_headers = {"Authorization": f"token {GITHUB_ACCESS_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    pages_config = {"source": {"branch": source_branch, "path": "/"}}
    try:
        response = httpx.post(api_endpoint, headers=request_headers, json=pages_config, timeout=30.0)
        if response.status_code in (201, 204):
            print("✅ Pages hosting activated for", repo_identifier)
            return True
        else:
            print("Pages API response:", response.status_code, response.text)
            return False
    except Exception as e:
        print("Failed to activate Pages hosting:", e)
        return False

def generate_license_content(owner_name=None):
    current_year = datetime.utcnow().year
    license_owner = owner_name or REPOSITORY_OWNER or "Project Owner"
    return f"""MIT License

Copyright (c) {current_year} {license_owner}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""