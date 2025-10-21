import git
from datetime import datetime

class GitHandler:
    def __init__(self, repo_path):
        self.repo = git.Repo(repo_path)

    def auto_commit(self, filepath, message):
        """Commit changes to git"""
        try:
            self.repo.index.add([filepath])
            self.repo.index.commit(message)
            return True
        except Exception as e:
            print(f"Git commit error: {e}")
            return False

    def push_changes(self):
        """Push to remote"""
        try:
            origin = self.repo.remote('origin')
            origin.push()
            return True
        except Exception as e:
            print(f"Git push error: {e}")
            return False

    def pull_changes(self):
        """Pull from remote"""
        try:
            origin = self.repo.remote('origin')
            origin.pull()
            return True
        except Exception as e:
            print(f"Git pull error: {e}")
            return False

    def get_file_history(self, filepath, limit=10):
        """Get commit history for file"""
        commits = list(self.repo.iter_commits(paths=filepath, max_count=limit))
        return [{
            'hash': c.hexsha[:7],
            'message': c.message.strip(),
            'date': datetime.fromtimestamp(c.committed_date).strftime('%Y-%m-%d %H:%M'),
            'author': str(c.author)
        } for c in commits]
