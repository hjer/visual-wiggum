#!/bin/bash
set -e

# Trust the workspace directory
git config --global --add safe.directory /workspaces/visual-wiggum

# Set git identity
git config --global user.name "${GIT_USER_NAME:-spec-view-bot}"
git config --global user.email "${GIT_USER_EMAIL:-bot@spec-view}"

# Configure git to use GH_TOKEN for HTTPS auth
if [ -n "${GH_TOKEN:-}" ]; then
    gh auth setup-git
fi
