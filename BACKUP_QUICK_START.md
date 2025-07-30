# 🚀 Quick Backup Guide

## 💨 **Super Fast Usage**

### **Git Bash / Linux / macOS:**
```bash
bash backup.sh
```

### **Windows Command Prompt:**
```cmd
backup.bat
```

---

## 📦 **What You Get**

✅ **259KB compressed backup** (vs ~500MB full project)  
✅ **All source code** (backend + frontend)  
✅ **Memory bank documentation**  
✅ **Configuration files**  
✅ **Emergency recovery procedures**  

❌ **Excluded**: node_modules, vector databases, cache files

---

## 🔄 **Quick Restore**

```bash
# 1. Extract
tar -xzf backups/RAG_backup_YYYYMMDD_HHMMSS.tar.gz

# 2. Dependencies  
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# 3. Start
bash start.sh

# 4. Re-upload documents
```

---

## ⚡ **Git Bash Note**

**If you get "rsync: command not found":**
- ✅ **Fixed**: Use `bash backup.sh` instead of `./backup.sh`
- ✅ **Works**: Standard Unix commands (cp, rm, find)
- ✅ **Tested**: Windows Git Bash compatible

---

## 📊 **Example Output**

```
🚀 Starting Enterprise RAG System Backup...
   📂 Backend code...
   🎨 Frontend code...
   🧠 Memory bank...
✅ Backup completed successfully!
📦 Backup file: backups/RAG_backup_20250627_162525.tar.gz
📊 Size: 260K
```

**🎯 Backup system is bulletproof and ready to use!** 