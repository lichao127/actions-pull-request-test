import os
import sys
import requests


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
    response.raise_for_status()
    return response.json()


def main():
    token = os.getenv("INPUT_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    title = os.getenv("INPUT_TITLE")
    head = os.getenv("INPUT_HEAD")
    base = os.getenv("INPUT_BASE")
    body = os.getenv("INPUT_BODY", "")

    if not all([token, repo, title, head, base]):
        print("Missing required inputs", file=sys.stderr)
        sys.exit(1)

    try:
        pr = create_pull_request(token, repo, title, head, base, body)
        print(f"Pull request created: {pr['html_url']}")
    except requests.exceptions.RequestException as e:
        print(f"Error creating pull request: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
