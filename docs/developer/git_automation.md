# Git Workflow Automation Guide

This document explains how to use the Git workflow automation script to streamline your development process with the CityPulse project.

## Overview

The `git_workflow.py` script automates common Git operations according to our established workflow, ensuring consistency and reducing manual errors. It implements the branching strategy and commit message conventions defined in our [Git Workflow Guide](git_workflow.md).

## Installation

1. Make sure the script is executable:

```bash
chmod +x scripts/git_workflow.py
```

2. For convenience, you may want to create a symbolic link to the script in a directory that's in your PATH:

```bash
ln -s $(pwd)/scripts/git_workflow.py /usr/local/bin/citypulse-git
```

## Commands

### Starting a Feature

To start working on a new feature:

```bash
./scripts/git_workflow.py feature my-feature-name
```

This will:
1. Switch to the `develop` branch
2. Pull the latest changes
3. Create a new branch called `feature/my-feature-name`
4. Switch to the new branch

### Making Commits

To commit changes with a standardized commit message:

```bash
./scripts/git_workflow.py commit feat data-collection "Add OSM POI collector" --body "Implemented collector for downloading Points of Interest from OpenStreetMap" --issue 42
```

This will create a commit with the message:

```
feat(data-collection): Add OSM POI collector

Implemented collector for downloading Points of Interest from OpenStreetMap

Closes #42
```

Available commit types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Changes to build process or auxiliary tools

### Pushing Changes

To push your current branch to the remote repository:

```bash
./scripts/git_workflow.py push
```

This will push your branch and set up tracking if it's the first push.

### Creating Pull Requests

To create a pull request for your current branch:

```bash
./scripts/git_workflow.py pr "Add OSM POI collector" --body "This PR implements the collector for downloading Points of Interest from OpenStreetMap"
```

Note: This requires the GitHub CLI to be installed and authenticated.

### Finishing a Feature

When you've completed work on a feature and want to merge it into the `develop` branch:

```bash
./scripts/git_workflow.py feature my-feature-name --finish
```

This will:
1. Push any remaining changes to the feature branch
2. Switch to the `develop` branch
3. Pull the latest changes
4. Merge the feature branch into `develop` with a proper merge commit
5. Push the changes to the remote `develop` branch
6. Delete the local and remote feature branches

### Managing Releases

To create a new release branch:

```bash
./scripts/git_workflow.py release 1.0.0
```

To finish a release:

```bash
./scripts/git_workflow.py release 1.0.0 --finish
```

This will:
1. Merge the release branch into `main`
2. Create a version tag
3. Merge the release branch into `develop`
4. Delete the release branch

### Checking Status

To check the current branch and status:

```bash
./scripts/git_workflow.py status
```

## Working with Bugfixes

To start working on a bugfix:

```bash
./scripts/git_workflow.py bugfix issue-description
```

This works similarly to the feature command, creating a branch called `bugfix/issue-description`.

## Examples

### Complete Feature Workflow

```bash
# Start a new feature
./scripts/git_workflow.py feature add-poi-collector

# Make changes to the code...

# Commit changes
./scripts/git_workflow.py commit feat data-collection "Add OSM POI collector"

# Push changes
./scripts/git_workflow.py push

# Create a pull request
./scripts/git_workflow.py pr "Add OSM POI collector"

# After PR is reviewed and approved, finish the feature
./scripts/git_workflow.py feature add-poi-collector --finish
```

### Release Workflow

```bash
# Create a release branch
./scripts/git_workflow.py release 1.0.0

# Make any final adjustments...

# Commit changes
./scripts/git_workflow.py commit chore release "Bump version to 1.0.0"

# Push changes
./scripts/git_workflow.py push

# Finish the release
./scripts/git_workflow.py release 1.0.0 --finish
```

## Troubleshooting

If you encounter merge conflicts, the script will notify you. You'll need to resolve the conflicts manually:

1. Fix the conflicts in the affected files
2. Stage the resolved files with `git add`
3. Complete the merge with `git commit`
4. Push the changes with `./scripts/git_workflow.py push`

If you encounter any other issues, run the script with the `--help` flag to see usage information:

```bash
./scripts/git_workflow.py --help
``` 