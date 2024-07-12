import os
import sys
import requests
import base64
from datetime import datetime

ACCEPT_HEADER = "application/vnd.github.v3+json"


def create_branch(token, repo, branch, base_branch):
    url = f"https://api.github.com/repos/{repo}/git/refs"
    headers = {
        "Authorization": f"token {token}",
        "Accept": ACCEPT_HEADER,
    }
    
    # Get the SHA of the base branch
    base_url = f"https://api.github.com/repos/{repo}/git/refs/heads/{base_branch}"
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    base_sha = response.json()["object"]["sha"]

    payload = {
        "ref": f"refs/heads/{branch}",
        "sha": base_sha
    }

    # create new branch
    response = requests.post(url, json=payload, headers=headers)
    # 422 is when entity exists
    if response.status_code == 422:
        return None
    else:
        response.raise_for_status()


def get_file_sha(token, repo, path, branch):
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": ACCEPT_HEADER,
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    elif response.status_code == 404:
        return None
    elif response.status_code == 422:
        return None
    else:
        response.raise_for_status()


def commit_file(token, repo, path, content, message, branch):
    sha = get_file_sha(token, repo, path, branch)
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": ACCEPT_HEADER,
    }
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
        "sha": ""
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 422:
       return

    response.raise_for_status()


def create_pull_request(token, repo, title, head, base, body=""):
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": ACCEPT_HEADER,
    }
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
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
    file_path = os.getenv("INPUT_FILE_PATH")
    commit_message = os.getenv("INPUT_COMMIT_MESSAGE")

    if not all([token, repo, title, head, base, file_path, commit_message]):
        print("Missing required inputs", file=sys.stderr)
        sys.exit(1)

    print(f"Checking for changes in file: {file_path} on branch: {head}")

    # generate new content
    now = datetime.now()
    new_content = now.strftime("%Y-%m-%d-%H-%M")

    try:
        sha = get_file_sha(token, repo, file_path, head)

        if sha:
            url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={head}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": ACCEPT_HEADER,
            }

            response = requests.get(url, headers=headers)
            current_content = response.json()["content"].strip()

            if current_content == new_content:
                print("No changes detected. Exiting.")
                sys.exit(0)

        print(f"Creating branch if not exist.")
        create_branch(token, repo, head, base)

        print("Changes detected. Committing and creating pull request.")

        commit_file(token, repo, file_path, new_content, commit_message, head)
        pr = create_pull_request(token, repo, title, head, base, body)
        print(f"Pull request created: {pr['html_url']}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
