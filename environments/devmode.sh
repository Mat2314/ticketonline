#!/bin/bash

# Change docker environment to DEVELOPMENT MODE
echo "Przechodzenie w tryb developerski..."

cp DevFiles/docker-compose.yml ../
cp DevFiles/Dockerfile ../

echo "Tryb developerski gotowy!"
