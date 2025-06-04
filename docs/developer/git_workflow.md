# Git Workflow Guide for CityPulse

This document outlines the Git workflow for the CityPulse project to ensure consistent version control practices.

## Repository Structure

The CityPulse project is hosted on GitHub: [https://github.com/yosrjdly/cityPulse](https://github.com/yosrjdly/cityPulse)

## Branching Strategy

We follow a simplified Git Flow branching model:

| Branch Type | Naming Convention | Purpose |
|-------------|------------------|---------|
| `main` | N/A | Production-ready code |
| `develop` | N/A | Integration branch for features |
| `feature/*` | `feature/feature-name` | New features |
| `bugfix/*` | `bugfix/issue-description` | Bug fixes |
| `release/*` | `release/vX.Y.Z` | Release preparation |
| `hotfix/*` | `hotfix/issue-description` | Urgent production fixes |

### Branch Lifecycle

1. **Feature Branches**
   - Created from: `develop`
   - Merged back into: `develop`
   - Naming: `feature/feature-name`

2. **Bugfix Branches**
   - Created from: `develop`
   - Merged back into: `develop`
   - Naming: `bugfix/issue-description`

3. **Release Branches**
   - Created from: `develop`
   - Merged back into: `develop` AND `main`
   - Naming: `release/vX.Y.Z`

4. **Hotfix Branches**
   - Created from: `main`
   - Merged back into: `develop` AND `main`
   - Naming: `hotfix/issue-description`

## Commit Message Guidelines

Follow these guidelines for clear and useful commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semi-colons, etc.)
- **refactor**: Code changes that neither fix bugs nor add features
- **perf**: Performance improvements
- **test**: Adding or modifying tests
- **chore**: Changes to build process or auxiliary tools

### Examples

```
feat(data-collection): implement OSM POI collector

Add collector for downloading Points of Interest from OpenStreetMap.
Includes rate limiting and error handling.

Closes #45
```

```
fix(analysis): correct isochrone calculation algorithm

Fixed incorrect travel time estimates in the isochrone calculation.

Fixes #123
```

## Pull Request Process

1. Create a branch from the appropriate base branch
2. Make your changes in small, logical commits
3. Push your branch to GitHub
4. Create a Pull Request (PR) to the appropriate target branch
5. Ensure the PR description clearly describes the changes
6. Request reviews from team members
7. Address review comments
8. Once approved, merge the PR

## Code Review Guidelines

When reviewing code, check for:

1. **Functionality**: Does the code work as intended?
2. **Quality**: Is the code well-written and maintainable?
3. **Style**: Does the code follow project style guidelines?
4. **Tests**: Are there appropriate tests?
5. **Documentation**: Is the code properly documented?

## Tagging and Releases

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards-compatible manner
- **PATCH**: Backwards-compatible bug fixes

### Release Process

1. Create a release branch: `release/vX.Y.Z`
2. Make any final adjustments and version bumps
3. Merge to `main`
4. Tag the merge commit on `main` with the version: `vX.Y.Z`
5. Merge back to `develop`

## Getting Started

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yosrjdly/cityPulse.git
cd cityPulse

# Set up remote
git remote add origin https://github.com/yosrjdly/cityPulse.git

# Create develop branch
git checkout -b develop
git push -u origin develop
```

### Working on Features

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/my-feature

# Make changes, then commit
git add .
git commit -m "feat(component): add feature description"

# Push to remote
git push -u origin feature/my-feature

# Create PR on GitHub
```

## Handling Merge Conflicts

If you encounter merge conflicts:

1. Fetch the latest changes from the target branch
2. Merge the target branch into your branch
3. Resolve conflicts locally
4. Commit the resolved changes
5. Push to your branch

```bash
git fetch origin
git merge origin/develop
# Resolve conflicts
git add .
git commit -m "Merge develop and resolve conflicts"
git push
```

## Git Best Practices

1. **Commit Often**: Make small, focused commits
2. **Pull Before Push**: Always pull the latest changes before pushing
3. **Use Branches**: Never work directly on `main` or `develop`
4. **Write Good Messages**: Follow the commit message guidelines
5. **Review Your Changes**: Use `git diff` to review changes before committing 