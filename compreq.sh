#!/bin/env bash

set -e

echo 1
git checkout jesper/compreq
# git checkout main
# git pull --rebase origing main
if ! git checkout -b compreq; then
    git branch -D compreq
    git checkout -b compreq
fi
echo 2
poetry run python -m requirements
echo 3
if [[ $(git status --porcelain) ]]; then
    echo 4
    git commit -am "Update requirements."
    echo 5
    git push origin +compreq
    echo 6
    gh pr create --title "Update requirements" --fill
    echo 7
    false
    echo 8
fi
echo 1000
