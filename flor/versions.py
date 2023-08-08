from .constants import *

from git.repo import Repo
from git.exc import InvalidGitRepositoryError


def git_commit(message="Auto-commit"):
    try:
        # Get the current working directory and initialize a Repo object
        repo = Repo(CURRDIR)

        # Check if there are any uncommitted changes
        if repo.is_dirty():
            # Add all untracked files and changes to tracked files
            repo.git.add(A=True)

            # Commit the changes
            repo.git.commit(m=message)
            print("Changes committed successfully")
        else:
            print("No changes to commit")
    except InvalidGitRepositoryError:
        print("Not a valid Git repository")
    except Exception as e:
        print(f"An error occurred while committing: {e}")


def current_branch():
    try:
        repo = Repo(CURRDIR)
        return repo.active_branch.name
    except InvalidGitRepositoryError:
        return None


def to_shadow():
    try:
        repo = Repo(CURRDIR)
        branch = repo.active_branch.name
        if branch.startswith(SHADOW_BRANCH_PREFIX):
            print("Branch already has the 'flor.' prefix, continuing...")
            return
        else:
            base_shadow_name = "flor.shadow"
            new_branch_name = base_shadow_name
            suffix = 1

            # Check if the branch name exists and increment the suffix until a unique name is found
            while any(b.name == new_branch_name for b in repo.branches):
                new_branch_name = f"{base_shadow_name}{suffix}"
                suffix += 1

            # Create a new branch with the unique name
            repo.git.checkout("-b", new_branch_name)
            print(f"Created and switched to new branch: {new_branch_name}")
    except InvalidGitRepositoryError:
        print("Not a valid Git repository")
    except Exception as e:
        print(f"An error occurred while processing the branch: {e}")
