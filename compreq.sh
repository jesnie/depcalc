#!/bin/env bash

set -e

echo 1
git checkout jesper/compreq
# git fetch origin main
# git checkout main
# git pull --rebase origin main
if ! git checkout -b compreq; then
    git branch -D compreq
    git checkout -b compreq
fi
echo 2
poetry run python -m requirements
echo 3
if [[ $(git status --porcelain) ]]; then
    echo 4
    poetry update
    git \
        -c "user.name=Update requirements bot" \
        -c "user.email=none" \
        commit \
        -am "Update requirements."
    echo 5
    git push origin +compreq
    echo 6
    gh pr create \
       --title "Update requirements" \
       --body "Automatic update of requirements."
    echo 7
    false
    echo 8
fi
echo 1000
