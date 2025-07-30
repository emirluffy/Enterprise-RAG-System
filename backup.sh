#!/bin/bash

# 🚀 Enterprise RAG System - Smart Backup Script
# Automatically backs up essential files with timestamp and compression
# Usage: ./backup.sh

set -e  # Exit on any error

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backups"
PROJECT_NAME="RAG"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}"
TEMP_DIR="temp_backup_${TIMESTAMP}"

echo -e "${BLUE}🚀 Starting Enterprise RAG System Backup...${NC}"
echo -e "${YELLOW}📅 Timestamp: ${TIMESTAMP}${NC}"

# Create backups directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}📁 Creating backups directory...${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# Create temporary directory for backup preparation
echo -e "${YELLOW}🔧 Preparing backup in temporary directory...${NC}"
mkdir -p "$TEMP_DIR"

# Essential directories and files to backup
echo -e "${BLUE}📋 Copying essential files...${NC}"

# Backend essentials (exclude unnecessary files) - COMPREHENSIVE COPY
if [ -d "backend" ]; then
    echo "   📂 Backend code..."
    mkdir -p "$TEMP_DIR/backend"
    
    # Copy ALL backend files and directories first
    echo "   🔄 Copying all backend files..."
    
    # Use rsync for better copying with exclusions (if available), otherwise use cp
    if command -v rsync >/dev/null 2>&1; then
        rsync -av backend/ "$TEMP_DIR/backend/" \
            --exclude="__pycache__" \
            --exclude="*.pyc" \
            --exclude="*.pyo" \
            --exclude="*.log" \
            --exclude="*.tmp" \
            --exclude="persistent_vector_db" \
            --exclude="local_vector_db" \
            --exclude="test_persistent_db" \
            --exclude=".pytest_cache" \
            --exclude=".venv" \
            --exclude="debug_context.txt" \
            --exclude="backend.log" \
            --quiet
    else
        # Fallback to cp with manual cleanup
        cp -r backend/. "$TEMP_DIR/backend/"
        
        # Then selectively remove what we don't want
        echo "   🧹 Removing unnecessary files..."
        find "$TEMP_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find "$TEMP_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true
        find "$TEMP_DIR/backend" -name "*.pyo" -delete 2>/dev/null || true
        find "$TEMP_DIR/backend" -name "*.log" -delete 2>/dev/null || true
        find "$TEMP_DIR/backend" -name "*.tmp" -delete 2>/dev/null || true
        rm -rf "$TEMP_DIR/backend/persistent_vector_db" 2>/dev/null || true
        rm -rf "$TEMP_DIR/backend/local_vector_db" 2>/dev/null || true
        rm -rf "$TEMP_DIR/backend/test_persistent_db" 2>/dev/null || true
        rm -rf "$TEMP_DIR/backend/.pytest_cache" 2>/dev/null || true
        rm -rf "$TEMP_DIR/backend/.venv" 2>/dev/null || true
        rm -f "$TEMP_DIR/backend/debug_context.txt" 2>/dev/null || true
        rm -f "$TEMP_DIR/backend/backend.log" 2>/dev/null || true
    fi
    
    # Count what we actually copied
    BACKEND_COUNT=$(find "$TEMP_DIR/backend" -maxdepth 1 -type f -o -type d | wc -l)
    echo "   ✅ Backed up $((BACKEND_COUNT-1)) backend items"
    
    # Debug: List what was actually copied
    echo "   🔍 Backend items backed up:"
    find "$TEMP_DIR/backend" -maxdepth 1 -type f -o -type d | sed 's|.*backend/||' | sort | sed 's/^/      ✓ /'
fi

# Frontend essentials (exclude node_modules and build artifacts) - COMPREHENSIVE COPY
if [ -d "frontend" ]; then
    echo "   🎨 Frontend code..."
    mkdir -p "$TEMP_DIR/frontend"
    
    # Copy ALL frontend files and directories first
    echo "   🔄 Copying all frontend files..."
    cp -r frontend/. "$TEMP_DIR/frontend/"
    
    # Then selectively remove what we don't want
    echo "   🧹 Removing unnecessary files..."
    rm -rf "$TEMP_DIR/frontend/node_modules" 2>/dev/null || true
    rm -rf "$TEMP_DIR/frontend/dist" 2>/dev/null || true
    rm -rf "$TEMP_DIR/frontend/build" 2>/dev/null || true
    rm -rf "$TEMP_DIR/frontend/.vite" 2>/dev/null || true
    rm -rf "$TEMP_DIR/frontend/.turbo" 2>/dev/null || true
    rm -rf "$TEMP_DIR/frontend/.next" 2>/dev/null || true
    find "$TEMP_DIR/frontend" -name "*.log" -delete 2>/dev/null || true
    
    # Count what we actually copied
    FRONTEND_COUNT=$(find "$TEMP_DIR/frontend" -maxdepth 1 -type f -o -type d | wc -l)
    echo "   ✅ Backed up $((FRONTEND_COUNT-1)) frontend items"
fi

# Memory bank (critical for system understanding)
if [ -d "memory-bank" ]; then
    echo "   🧠 Memory bank..."
    cp -r memory-bank "$TEMP_DIR/"
    MEMORY_COUNT=$(find "$TEMP_DIR/memory-bank" -maxdepth 1 -type f | wc -l)
    echo "   ✅ Backed up $MEMORY_COUNT memory bank files"
fi

# Root level configuration files and scripts
echo "   ⚙️  Root configuration and scripts..."
ROOT_FILES=0

# Copy all important root files
for file in start.sh start.bat README.md pyproject.toml package.json requirements.txt requirements_local.txt .gitignore .dockerignore; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
        ROOT_FILES=$((ROOT_FILES + 1))
        echo "     ✓ $file"
    fi
done

# Copy all backup-related files
for file in backup.sh backup.bat BACKUP_QUICK_START.md BACKUP_USAGE.md; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
        ROOT_FILES=$((ROOT_FILES + 1))
        echo "     ✓ $file"
    fi
done

echo "   ✅ Backed up $ROOT_FILES root files"

# Cursor rules (important project context)
if [ -d ".cursor" ]; then
    echo "   🎯 Cursor rules..."
    cp -r .cursor "$TEMP_DIR/"
    CURSOR_COUNT=$(find "$TEMP_DIR/.cursor" -type f | wc -l)
    echo "   ✅ Backed up $CURSOR_COUNT cursor files"
fi

# Environment files (excluding secrets)
ENV_FILES=0
for file in .env.example .env.rotation.example; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
        ENV_FILES=$((ENV_FILES + 1))
        echo "     ✓ $file"
    fi
done
if [ $ENV_FILES -gt 0 ]; then
    echo "   ✅ Backed up $ENV_FILES environment files"
fi

# Critical fixes log if exists
if [ -f "CRITICAL_FIXES_LOG.md" ]; then
    echo "   🚨 Critical fixes documentation..."
    cp CRITICAL_FIXES_LOG.md "$TEMP_DIR/"
fi

# Test files and directories (if they exist)
if [ -d "test_ppt_files" ]; then
    echo "   🧪 Test files..."
    cp -r test_ppt_files "$TEMP_DIR/"
    TEST_COUNT=$(find "$TEMP_DIR/test_ppt_files" -type f | wc -l)
    echo "   ✅ Backed up $TEST_COUNT test files"
fi

# Any other important files
for file in *.txt *.md *.json; do
    if [ -f "$file" ] && [ ! -f "$TEMP_DIR/$file" ]; then
        cp "$file" "$TEMP_DIR/" 2>/dev/null || true
    fi
done

# Create backup info file with comprehensive details
echo -e "${YELLOW}📝 Creating backup info...${NC}"

# Count total items in backup
TOTAL_ITEMS=$(find "$TEMP_DIR" -type f | wc -l)
TOTAL_DIRS=$(find "$TEMP_DIR" -type d | wc -l)

cat > "$TEMP_DIR/BACKUP_INFO.md" << EOF
# 📦 RAG System Backup Information

## 🕐 Backup Details
- **Created**: $(date)
- **Timestamp**: ${TIMESTAMP}
- **System**: $(uname -a)
- **User**: $(whoami)
- **Total Files**: $TOTAL_ITEMS
- **Total Directories**: $TOTAL_DIRS

## 📋 Backup Contents
- ✅ Backend code (Python/FastAPI) - Complete structure
- ✅ Frontend code (React/TypeScript) - Complete structure  
- ✅ Memory bank documentation
- ✅ Configuration files
- ✅ Startup scripts
- ✅ Backup scripts and documentation
- ✅ Cursor rules and project context
- ✅ Test files and sample data
- ✅ All markdown documentation

## ❌ Excluded Items
- Node modules (can be restored with npm install)
- Python cache files (__pycache__)
- Virtual environments (.venv)
- Vector databases (can be rebuilt)
- Log files
- Temporary files
- Build artifacts

## 🔍 Backup Verification
Original backend items: $(find backend -maxdepth 1 -type f -o -type d | wc -l)
Backed up backend items: $(find "$TEMP_DIR/backend" -maxdepth 1 -type f -o -type d 2>/dev/null | wc -l || echo "0")

## 🔄 Restore Instructions
1. Extract this backup to desired location
2. Run: cd frontend && npm install
3. Run: cd backend && pip install -r requirements.txt
4. Run: ./start.sh
5. Re-upload documents to rebuild vector database

## 🚨 Emergency Recovery
If system breaks, this backup contains all essential code and configurations.
Check CRITICAL_FIXES_LOG.md for common issues and solutions.
EOF

# Create compressed backup
echo -e "${BLUE}📦 Creating compressed backup...${NC}"
cd "$TEMP_DIR"
tar -czf "../$BACKUP_DIR/$BACKUP_NAME.tar.gz" .
cd ..

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)

# Cleanup temporary directory
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -rf "$TEMP_DIR"

# Success message with verification
echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo -e "${GREEN}📦 Backup file: $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
echo -e "${GREEN}📊 Size: $BACKUP_SIZE${NC}"
echo -e "${GREEN}📁 Total items backed up: $TOTAL_ITEMS files, $TOTAL_DIRS directories${NC}"
echo ""

# Verification check
echo -e "${BLUE}🔍 Backup verification:${NC}"
ORIGINAL_BACKEND=$(find backend -maxdepth 1 -type f -o -type d | wc -l)
echo -e "${YELLOW}   Original backend items: $((ORIGINAL_BACKEND-1))${NC}"

if [ -d "frontend" ]; then
    ORIGINAL_FRONTEND=$(find frontend -maxdepth 1 -type f -o -type d | wc -l)
    echo -e "${YELLOW}   Original frontend items: $((ORIGINAL_FRONTEND-1))${NC}"
fi

echo ""
echo -e "${BLUE}🔄 To restore this backup:${NC}"
echo -e "${YELLOW}   1. Extract: tar -xzf $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
echo -e "${YELLOW}   2. Install dependencies: cd frontend && npm install${NC}"
echo -e "${YELLOW}   3. Install Python deps: cd backend && pip install -r requirements.txt${NC}"
echo -e "${YELLOW}   4. Start system: ./start.sh${NC}"
echo ""

# List recent backups
echo -e "${BLUE}📚 Recent backups:${NC}"
ls -lah "$BACKUP_DIR" | tail -5

echo -e "${GREEN}🎉 Backup process complete!${NC}" 