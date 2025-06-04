#!/usr/bin/env python
"""
Git Workflow Automation Script for CityPulse

This script automates common Git workflow operations to ensure consistency
and reduce manual errors when working with the CityPulse repository.
"""
import os
import sys
import argparse
import subprocess
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class BranchType(Enum):
    """Enum for branch types."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    RELEASE = "release"
    HOTFIX = "hotfix"


class CommitType(Enum):
    """Enum for commit types."""
    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"


class GitWorkflow:
    """Class to manage Git workflow operations."""

    def __init__(self, repo_path: str = "."):
        """Initialize the GitWorkflow class.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        if not self._is_git_repo():
            raise ValueError(f"The directory {self.repo_path} is not a Git repository")
        
        # Change to the repository directory
        os.chdir(self.repo_path)
    
    def _is_git_repo(self) -> bool:
        """Check if the directory is a Git repository.
        
        Returns:
            True if it's a Git repository, False otherwise
        """
        return (self.repo_path / ".git").is_dir()
    
    def _run_command(self, command: List[str], check: bool = True) -> Tuple[int, str, str]:
        """Run a shell command and return the result.
        
        Args:
            command: Command to run as a list of strings
            check: Whether to raise an exception if the command fails
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(command)}")
            print(f"Error: {e.stderr}")
            if check:
                raise
            return e.returncode, e.stdout, e.stderr
    
    def get_current_branch(self) -> str:
        """Get the name of the current branch.
        
        Returns:
            Name of the current branch
        """
        _, stdout, _ = self._run_command(["git", "branch", "--show-current"])
        return stdout.strip()
    
    def checkout_branch(self, branch_name: str, create: bool = False) -> bool:
        """Checkout a branch, optionally creating it.
        
        Args:
            branch_name: Name of the branch
            create: Whether to create the branch if it doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        command = ["git", "checkout"]
        if create:
            command.append("-b")
        command.append(branch_name)
        
        try:
            self._run_command(command)
            print(f"Switched to branch '{branch_name}'")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_branch(self, branch_type: BranchType, name: str) -> bool:
        """Create a new branch of the specified type.
        
        Args:
            branch_type: Type of the branch (feature, bugfix, etc.)
            name: Name of the branch
            
        Returns:
            True if successful, False otherwise
        """
        # Determine base branch
        if branch_type in [BranchType.FEATURE, BranchType.BUGFIX]:
            base_branch = "develop"
        elif branch_type == BranchType.HOTFIX:
            base_branch = "main"
        elif branch_type == BranchType.RELEASE:
            base_branch = "develop"
        else:
            print(f"Unknown branch type: {branch_type}")
            return False
        
        # Make sure we're on the right base branch
        current_branch = self.get_current_branch()
        if current_branch != base_branch:
            print(f"Switching to {base_branch} branch...")
            self.checkout_branch(base_branch)
            
            # Pull latest changes
            print(f"Pulling latest changes from {base_branch}...")
            self._run_command(["git", "pull", "origin", base_branch])
        
        # Create new branch
        branch_name = f"{branch_type.value}/{name}"
        print(f"Creating new branch: {branch_name}")
        return self.checkout_branch(branch_name, create=True)
    
    def commit_changes(self, 
                      commit_type: CommitType, 
                      scope: str, 
                      message: str, 
                      body: Optional[str] = None, 
                      issue: Optional[int] = None) -> bool:
        """Commit changes with a standardized commit message.
        
        Args:
            commit_type: Type of commit (feat, fix, etc.)
            scope: Scope of the commit (component affected)
            message: Short commit message
            body: Optional detailed description
            issue: Optional issue number to reference
            
        Returns:
            True if successful, False otherwise
        """
        # Build commit message
        commit_msg = f"{commit_type.value}({scope}): {message}"
        
        if body:
            commit_msg += f"\n\n{body}"
        
        if issue:
            commit_msg += f"\n\nCloses #{issue}"
        
        # Stage all changes
        print("Staging changes...")
        self._run_command(["git", "add", "."])
        
        # Commit changes
        print(f"Committing with message: {commit_msg.split(chr(10))[0]}")
        try:
            with open(".git_commit_msg.tmp", "w") as f:
                f.write(commit_msg)
            self._run_command(["git", "commit", "-F", ".git_commit_msg.tmp"])
            os.remove(".git_commit_msg.tmp")
            return True
        except Exception as e:
            print(f"Failed to commit changes: {e}")
            return False
    
    def push_branch(self, set_upstream: bool = True) -> bool:
        """Push the current branch to the remote repository.
        
        Args:
            set_upstream: Whether to set the upstream branch
            
        Returns:
            True if successful, False otherwise
        """
        branch = self.get_current_branch()
        command = ["git", "push"]
        
        if set_upstream:
            command.extend(["-u", "origin", branch])
        else:
            command.extend(["origin", branch])
        
        try:
            print(f"Pushing branch {branch} to remote...")
            self._run_command(command)
            print(f"Successfully pushed {branch} to remote")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_pull_request(self, title: str, body: str) -> bool:
        """Create a pull request for the current branch.
        
        Note: This requires the GitHub CLI to be installed and authenticated.
        
        Args:
            title: Title of the pull request
            body: Description of the pull request
            
        Returns:
            True if successful, False otherwise
        """
        branch = self.get_current_branch()
        
        # Determine target branch
        if branch.startswith("feature/") or branch.startswith("bugfix/"):
            target = "develop"
        elif branch.startswith("hotfix/"):
            target = "main"
        elif branch.startswith("release/"):
            target = "main"
        else:
            print(f"Cannot determine target branch for {branch}")
            return False
        
        try:
            # Check if GitHub CLI is installed
            self._run_command(["gh", "--version"], check=False)
            
            # Create pull request
            print(f"Creating pull request from {branch} to {target}...")
            self._run_command([
                "gh", "pr", "create",
                "--base", target,
                "--head", branch,
                "--title", title,
                "--body", body
            ])
            return True
        except subprocess.CalledProcessError:
            print("Failed to create pull request. Make sure GitHub CLI is installed and authenticated.")
            print("You can create the pull request manually on GitHub.")
            return False
    
    def finish_feature(self, name: str) -> bool:
        """Finish a feature branch by merging it into develop.
        
        Args:
            name: Name of the feature
            
        Returns:
            True if successful, False otherwise
        """
        feature_branch = f"feature/{name}"
        
        # Make sure we're on the feature branch
        current_branch = self.get_current_branch()
        if current_branch != feature_branch:
            print(f"Switching to {feature_branch} branch...")
            if not self.checkout_branch(feature_branch):
                print(f"Branch {feature_branch} does not exist")
                return False
        
        # Push any remaining changes
        self.push_branch()
        
        # Switch to develop branch
        print("Switching to develop branch...")
        self.checkout_branch("develop")
        
        # Pull latest changes
        print("Pulling latest changes from develop...")
        self._run_command(["git", "pull", "origin", "develop"])
        
        # Merge feature branch
        print(f"Merging {feature_branch} into develop...")
        try:
            self._run_command(["git", "merge", "--no-ff", feature_branch, "-m", f"Merge feature/{name}"])
            
            # Push changes to develop
            print("Pushing changes to develop...")
            self._run_command(["git", "push", "origin", "develop"])
            
            # Delete feature branch
            print(f"Deleting {feature_branch} branch...")
            self._run_command(["git", "branch", "-d", feature_branch])
            self._run_command(["git", "push", "origin", "--delete", feature_branch], check=False)
            
            return True
        except subprocess.CalledProcessError:
            print("Merge conflict detected. Please resolve conflicts manually.")
            return False
    
    def create_release(self, version: str) -> bool:
        """Create a release branch.
        
        Args:
            version: Version number (e.g., "1.0.0")
            
        Returns:
            True if successful, False otherwise
        """
        return self.create_branch(BranchType.RELEASE, f"v{version}")
    
    def finish_release(self, version: str) -> bool:
        """Finish a release by merging it into main and develop.
        
        Args:
            version: Version number (e.g., "1.0.0")
            
        Returns:
            True if successful, False otherwise
        """
        release_branch = f"release/v{version}"
        
        # Make sure we're on the release branch
        current_branch = self.get_current_branch()
        if current_branch != release_branch:
            print(f"Switching to {release_branch} branch...")
            if not self.checkout_branch(release_branch):
                print(f"Branch {release_branch} does not exist")
                return False
        
        # Push any remaining changes
        self.push_branch()
        
        # Switch to main branch
        print("Switching to main branch...")
        self.checkout_branch("main")
        
        # Pull latest changes
        print("Pulling latest changes from main...")
        self._run_command(["git", "pull", "origin", "main"])
        
        # Merge release branch into main
        print(f"Merging {release_branch} into main...")
        try:
            self._run_command(["git", "merge", "--no-ff", release_branch, "-m", f"Merge release v{version}"])
            
            # Create tag
            print(f"Creating tag v{version}...")
            self._run_command(["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"])
            
            # Push changes to main
            print("Pushing changes to main...")
            self._run_command(["git", "push", "origin", "main"])
            
            # Push tags
            print("Pushing tags...")
            self._run_command(["git", "push", "origin", "--tags"])
            
            # Switch to develop branch
            print("Switching to develop branch...")
            self.checkout_branch("develop")
            
            # Pull latest changes
            print("Pulling latest changes from develop...")
            self._run_command(["git", "pull", "origin", "develop"])
            
            # Merge release branch into develop
            print(f"Merging {release_branch} into develop...")
            self._run_command(["git", "merge", "--no-ff", release_branch, "-m", f"Merge release v{version}"])
            
            # Push changes to develop
            print("Pushing changes to develop...")
            self._run_command(["git", "push", "origin", "develop"])
            
            # Delete release branch
            print(f"Deleting {release_branch} branch...")
            self._run_command(["git", "branch", "-d", release_branch])
            self._run_command(["git", "push", "origin", "--delete", release_branch], check=False)
            
            return True
        except subprocess.CalledProcessError:
            print("Merge conflict detected. Please resolve conflicts manually.")
            return False


def parse_args():
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Git workflow automation for CityPulse")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start feature command
    feature_parser = subparsers.add_parser("feature", help="Start a new feature")
    feature_parser.add_argument("name", help="Name of the feature")
    feature_parser.add_argument("--finish", action="store_true", help="Finish the feature")
    
    # Start bugfix command
    bugfix_parser = subparsers.add_parser("bugfix", help="Start a new bugfix")
    bugfix_parser.add_argument("name", help="Name of the bugfix")
    
    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit changes")
    commit_parser.add_argument("type", choices=[t.value for t in CommitType], help="Type of commit")
    commit_parser.add_argument("scope", help="Scope of the commit")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument("--body", help="Detailed description")
    commit_parser.add_argument("--issue", type=int, help="Issue number to reference")
    
    # Push command
    push_parser = subparsers.add_parser("push", help="Push the current branch")
    
    # PR command
    pr_parser = subparsers.add_parser("pr", help="Create a pull request")
    pr_parser.add_argument("title", help="Title of the pull request")
    pr_parser.add_argument("--body", default="", help="Description of the pull request")
    
    # Release command
    release_parser = subparsers.add_parser("release", help="Manage releases")
    release_parser.add_argument("version", help="Version number (e.g., 1.0.0)")
    release_parser.add_argument("--finish", action="store_true", help="Finish the release")
    
    # Status command
    subparsers.add_parser("status", help="Show the current branch and status")
    
    return parser.parse_args()


def main():
    """Main function to run the script."""
    args = parse_args()
    
    try:
        workflow = GitWorkflow()
        
        if args.command == "feature":
            if args.finish:
                workflow.finish_feature(args.name)
            else:
                workflow.create_branch(BranchType.FEATURE, args.name)
        
        elif args.command == "bugfix":
            workflow.create_branch(BranchType.BUGFIX, args.name)
        
        elif args.command == "commit":
            commit_type = next(t for t in CommitType if t.value == args.type)
            workflow.commit_changes(commit_type, args.scope, args.message, args.body, args.issue)
        
        elif args.command == "push":
            workflow.push_branch()
        
        elif args.command == "pr":
            workflow.create_pull_request(args.title, args.body)
        
        elif args.command == "release":
            if args.finish:
                workflow.finish_release(args.version)
            else:
                workflow.create_release(args.version)
        
        elif args.command == "status":
            branch = workflow.get_current_branch()
            print(f"Current branch: {branch}")
            workflow._run_command(["git", "status"])
        
        else:
            print("Please specify a command. Run with --help for usage information.")
            return 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 