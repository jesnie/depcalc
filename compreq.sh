#!/bin/env bash

set -e

git fetch origin main
git checkout main
git pull --rebase origin main
if ! git checkout -b compreq; then
    git branch -D compreq
    git checkout -b compreq
fi
poetry run python -m requirements
if [[ $(git status --porcelain) ]]; then
    poetry update
    git \
        -c "user.name=Update requirements bot" \
        -c "user.email=none" \
        commit \
        -am "Update requirements."
    git push origin +compreq
    gh pr create \
       --title "Update requirements" \
       --body "Automatic update of requirements." \
       --reviewer jesnie
    false
fi
