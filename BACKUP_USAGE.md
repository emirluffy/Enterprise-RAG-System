# 🚀 Enterprise RAG System - Backup Guide

## 📦 Smart Backup System

Bu proje için özel olarak tasarlanmış akıllı backup sistemi, **sadece gerekli dosyaları** yedekler ve **gereksiz şişkinlikleri** (node_modules, vector DB, cache files) atlar.

---

## 🎯 **Quick Start**

### **Windows Users:**
```cmd
backup.bat
```

### **Linux/macOS/Git Bash Users:**
```bash
./backup.sh
```

---

## 📋 **Yedeklenen Dosyalar**

### ✅ **Dahil Edilen:**
- **Backend Code**: Python/FastAPI kaynak kodları
- **Frontend Code**: React/TypeScript kaynak kodları  
- **Memory Bank**: Kritik sistem dokümantasyonu
- **Configuration**: start.sh, start.bat, requirements.txt
- **Cursor Rules**: Proje context ve kuralları
- **Critical Fixes**: CRITICAL_FIXES_LOG.md

### ❌ **Hariç Tutulan:**
- **node_modules** (npm install ile geri yüklenebilir)
- **__pycache__** (Python cache dosyları)
- **Vector Databases** (dokümanlar yeniden yüklenebilir)
- **Log Files** (*.log)
- **Build Artifacts** (dist, build klasörleri)
- **Temporary Files** (*.tmp)

---

## 📁 **Backup Output**

### **Dosya Formatı:**
```
backups/RAG_backup_YYYYMMDD_HHMMSS.tar.gz  (Linux/macOS)
backups/RAG_backup_YYYYMMDD_HHMMSS.zip     (Windows)
```

### **Örnek:**
```
backups/RAG_backup_20250127_143022.tar.gz
```

---

## 🔄 **Restore Instructions**

### **1. Extract Backup:**
```bash
# Linux/macOS
tar -xzf backups/RAG_backup_YYYYMMDD_HHMMSS.tar.gz

# Windows
# Right-click → Extract All veya 7-Zip ile çıkar
```

### **2. Install Dependencies:**
```bash
# Frontend dependencies
cd frontend
npm install

# Backend dependencies  
cd ../backend
pip install -r requirements.txt
```

### **3. Start System:**
```bash
# Linux/macOS/Git Bash
./start.sh

# Windows
start.bat
```

### **4. Re-upload Documents:**
- Vector database dosyaları yedeklenmediği için
- Dokümanları tekrar upload etmen gerekiyor
- Sistema log in olduktan sonra dokümanları yeniden yükle

---

## 🚨 **Emergency Recovery**

### **Sistem Bozulduğunda:**

1. **🔍 Diagnose**: Logs'ta hata mesajlarını kontrol et
2. **📖 Check**: `CRITICAL_FIXES_LOG.md` dosyasını oku
3. **⚡ Quick Fix**: Bilinen patternleri uygula
4. **🔄 Restore**: Gerekirse backup'tan geri yükle

### **Common Issues:**
- **"truth value of an array"** → ChromaDB fix gerekli
- **"atalı girildiğinde"** → Chunking algorithm problemi  
- **"No text content found"** → Text extraction issue

---

## 📊 **Backup Size Guide**

### **Typical Sizes:**
- **Full Project**: ~200-500 MB (node_modules ile)
- **Smart Backup**: ~5-15 MB (optimized)
- **With Documents**: +2-10 MB (doküman sayısına göre)

### **Space Savings:**
- ✅ **95% smaller** than full backup
- ✅ **Instant restore** (no large downloads)
- ✅ **Version control friendly**

---

## 🔧 **Advanced Usage**

### **Automated Backups:**
```bash
# Daily backup (Linux/macOS crontab)
0 2 * * * cd /path/to/RAG && ./backup.sh

# Windows Task Scheduler ile backup.bat çalıştır
```

### **Custom Backup Location:**
```bash
# Edit backup.sh/backup.bat
BACKUP_DIR="custom_backup_location"
```

### **Include Additional Files:**
```bash
# backup.sh içinde ekle:
cp custom_file.txt "$TEMP_DIR/"
```

---

## 💡 **Best Practices**

### **📅 When to Backup:**
- ✅ **Before major changes**
- ✅ **After fixing critical bugs**  
- ✅ **Before system updates**
- ✅ **Weekly automatic backups**

### **🗂️ Backup Management:**
- Keep **last 5 backups** minimum
- Archive **monthly backups** to cloud
- Test **restore process** periodically
- Document **major changes** in backup notes

### **🔐 Security:**
- Backup files **don't include API keys**
- Store backups in **secure location**
- Encrypt backups for **sensitive projects**

---

## 🎉 **Success Examples**

### **Backup Creation:**
```
🚀 Starting Enterprise RAG System Backup...
📅 Timestamp: 20250127_143022
📁 Creating backups directory...
🔧 Preparing backup in temporary directory...
📋 Copying essential files...
   📂 Backend code...
   🎨 Frontend code...
   🧠 Memory bank...
   ⚙️ Configuration and scripts...
   🎯 Cursor rules...
📝 Creating backup info...
📦 Creating compressed backup...
🧹 Cleaning up temporary files...
✅ Backup completed successfully!
📦 Backup file: backups/RAG_backup_20250127_143022.tar.gz
📊 Size: 8.2M
```

### **Successful Restore:**
```
✅ Dependencies installed
✅ System started on http://localhost:8002
✅ Frontend running on http://localhost:5174
🎉 RAG System fully operational!
```

---

## 📞 **Support**

### **If Issues Occur:**
1. Check `BACKUP_INFO.md` in backup file
2. Review `CRITICAL_FIXES_LOG.md` 
3. Follow restore instructions step-by-step
4. Re-upload documents to rebuild vector database

### **Backup Script Location:**
- `backup.sh` - Linux/macOS/Git Bash
- `backup.bat` - Windows Command Prompt

**🎯 The backup system is designed to be bulletproof and fast!** 