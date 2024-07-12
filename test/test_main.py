import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
from main import (
    get_file_sha,
    create_branch,
    commit_file,
    create_pull_request,
    main
)

class TestMain(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='file content')
    def test_get_file_content(self, mock_file):
        content = get_file_content('test.txt')
        self.assertEqual(content, 'file content')

    @patch('main.requests.get')
    def test_get_file_sha_exists(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"sha": "12345"})
        sha = get_file_sha('token', 'repo', 'path', 'branch')
        self.assertEqual(sha, '12345')

    @patch('main.requests.get')
    def test_get_file_sha_not_found(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)
        sha = get_file_sha('token', 'repo', 'path', 'branch')
        self.assertIsNone(sha)

    @patch('main.requests.post')
    @patch('main.requests.get')
    def test_create_branch(self, mock_get, mock_post):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"object": {"sha": "base-sha"}})
        mock_post.return_value = MagicMock(status_code=201, json=lambda: {"ref": "refs/heads/new-branch"})
        branch = create_branch('token', 'repo', 'new-branch', 'base-branch')
        self.assertEqual(branch['ref'], 'refs/heads/new-branch')

    @patch('main.create_branch')
    @patch('main.requests.put')
    @patch('main.get_file_sha')
    def test_commit_file(self, mock_get_file_sha, mock_put, mock_create_branch):
        mock_get_file_sha.side_effect = [None, 'existing-sha']
        mock_put.side_effect = [
            MagicMock(status_code=404),
            MagicMock(status_code=201, json=lambda: {"content": {"html_url": "url"}})
        ]
        mock_create_branch.return_value = {"ref": "refs/heads/new-branch"}
        response = commit_file('token', 'repo', 'path', 'content', 'message', 'branch', 'base-branch')
        self.assertEqual(response['content']['html_url'], 'url')

    @patch('main.requests.post')
    def test_create_pull_request(self, mock_post):
        mock_post.return_value = MagicMock(status_code=201, json=lambda: {"html_url": "pr-url"})
        pr = create_pull_request('token', 'repo', 'title', 'head', 'base')
        self.assertEqual(pr['html_url'], 'pr-url')

    @patch('main.get_changed_files')
    @patch('main.commit_file')
    @patch('main.create_pull_request')
    @patch('main.get_file_content', return_value='file content')
    @patch.dict(os.environ, {
        "INPUT_TOKEN": "token",
        "GITHUB_REPOSITORY": "repo",
        "INPUT_TITLE": "title",
        "INPUT_HEAD": "head",
        "INPUT_BASE": "base",
        "INPUT_COMMIT_MESSAGE": "commit message"
    })
    def test_main(self, mock_create_pull_request, mock_commit_file, mock_get_changed_files):
        mock_get_changed_files.return_value = ['file1', 'file2']
        mock_create_pull_request.return_value = {"html_url": "pr-url"}
        with patch('builtins.print') as mock_print:
            main()
            mock_print.assert_any_call("Detecting changes...")
            mock_print.assert_any_call("Changes detected in the following files:")
            mock_print.assert_any_call("Committing changes and creating pull request.")
            mock_print.assert_any_call(f"Pull request created: pr-url")

if __name__ == '__main__':
    unittest.main()