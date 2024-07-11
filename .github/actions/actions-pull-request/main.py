import os
import sys
import subprocess
import requests
import base64
from datetime import datetime


def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {command}", file=sys.stderr)
        print(result.stderr.decode(), file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout.decode().strip()


def get_changed_files():
    changed_files = run_command("git diff --name-only HEAD~1 HEAD")
    return changed_files.splitlines()


def get_file_content(file_path):
    with open(file_path, "r") as file:
        return file.read()


def get_file_sha(token, repo, path, branch):
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    elif response.status_code == 404:
        return None
    else:
        response.raise_for_status()


def commit_file(token, repo, path, content, message, branch):
    sha = get_file_sha(token, repo, path, branch)
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def create_pull_request(token, repo, title, head, base, body=""):
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }

    response = requests.post(url, json=payload, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Request failed: {response.status_code} {response.text}", file=sys.stderr)
        raise e
    return response.json()


def main():
    token = os.getenv("INPUT_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    title = os.getenv("INPUT_TITLE")
    head = os.getenv("INPUT_HEAD")
    base = os.getenv("INPUT_BASE")
    body = os.getenv("INPUT_BODY", "")
    commit_message = os.getenv("INPUT_COMMIT_MESSAGE")

    # write a dummy file
    print('###########')
    print(repo,title,head,base,commit_message)
    if not all([token, repo, title, head, base, commit_message]):
        print("Missing required inputs", file=sys.stderr)
        sys.exit(1)

    print("Detecting changes...")

    try:
        changed_files = get_changed_files()
        if not changed_files:
            print("No changes detected. Exiting.")
            sys.exit(0)

        print("Changes detected in the following files:")
        for file_path in changed_files:
            print(file_path)
            file_content = get_file_content(file_path)
            commit_file(token, repo, file_path, file_content, commit_message, head)

        print("Committing changes and creating pull request.")
        pr = create_pull_request(token, repo, title, head, base, body)
        print(f"Pull request created: {pr['html_url']}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
