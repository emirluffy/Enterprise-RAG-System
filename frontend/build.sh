#!/bin/bash
# Vercel build script for frontend

echo "🚀 Building React frontend for production..."

# Install dependencies
npm install

# Build the project
npm run build

echo "✅ Frontend build completed!"
