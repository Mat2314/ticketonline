#!/bin/bash

# Change docker environment to PRODUCTION MODE
echo "Przechodzenie w tryb produkcyjny..."

rm ../docker-compose.yml ../Dockerfile

cp ProdFiles/docker-compose.yml ../
cp ProdFiles/Dockerfile ../

echo "Tryb produkcyjny gotowy!"
