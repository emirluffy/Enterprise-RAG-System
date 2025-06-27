# 🌐 Enterprise RAG System - Network Access Guide

## Şirket Bilgisayarından Erişim Konfigürasyonu

### 🎯 **Amaç**
- Kendi PC'nizdeki (localhost:5174) sisteme şirket bilgisayarından erişim
- PowerPoint (.pptx) dosya desteği ile doküman yükleme
- Güvenli ağ erişimi kurulumu

### 📡 **1. IP Address Configuration**

#### **A) PC'nizin IP Adresini Bulun:**
```bash
# Windows (PowerShell/CMD)
ipconfig

# Arayın: "IPv4 Address" 
# Örnek: 192.168.1.100
```

#### **B) .env Dosyasını Güncelleyin:**
```env
# Mevcut
FRONTEND_HOST=http://localhost:5174
BACKEND_CORS_ORIGINS=http://localhost:5174,http://localhost:5173

# Yeni (IP adresinizi kullanın)
FRONTEND_HOST=http://192.168.1.100:5174
BACKEND_CORS_ORIGINS=http://localhost:5174,http://localhost:5173,http://192.168.1.100:5174,http://YOUR_COMPANY_PC_IP:*
```

### 🔧 **2. Windows Firewall Configuration**

#### **A) Firewall Exception Ekleyin:**
```powershell
# PowerShell (Yönetici Olarak Çalıştırın)
New-NetFirewallRule -DisplayName "RAG Frontend" -Direction Inbound -Protocol TCP -LocalPort 5174 -Action Allow
New-NetFirewallRule -DisplayName "RAG Backend" -Direction Inbound -Protocol TCP -LocalPort 8002 -Action Allow
```

#### **B) Manuel Firewall Ayarı:**
1. **Windows Güvenlik** → **Güvenlik Duvarı ve ağ koruması**
2. **Gelişmiş ayarlar**
3. **Gelen Kuralları** → **Yeni Kural**
4. **Bağlantı Noktası** → **TCP** → **5174, 8002**
5. **Bağlantıya İzin Ver** → **Tüm Profiller**

### 🌐 **3. Network Discovery**

#### **A) Network Discovery Açın:**
```powershell
# PowerShell (Yönetici)
netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes
```

#### **B) Manuel Ayar:**
1. **Denetim Masası** → **Ağ ve İnternet** → **Ağ ve Paylaşım Merkezi**
2. **Gelişmiş paylaşım ayarlarını değiştir**
3. **Ağ bulma** → **Açık**
4. **Dosya ve yazıcı paylaşımı** → **Açık**

### 🚀 **4. Server Başlatma (Network Mode)**

#### **A) start.sh'ı Güncelleyin:**
```bash
#!/bin/bash
# Network access için start script

echo "🔥 Killing existing processes..."
taskkill //F //IM python.exe 2>/dev/null || true
taskkill //F //IM node.exe 2>/dev/null || true

echo "🎨 Starting Backend (Network Mode)..."
cd backend
python simple_server.py &
sleep 3

echo "🎨 Starting Frontend (Network Mode)..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5174 &

echo "✅ Servers starting in network mode!"
echo "🌐 Frontend: http://0.0.0.0:5174 (accessible from network)"
echo "🌐 Backend: http://0.0.0.0:8002"
echo "📱 Your IP Access: http://$(ipconfig | grep 'IPv4' | head -1 | awk '{print $14}'):5174"

wait
```

#### **B) Backend Network Config:**
```python
# backend/simple_server.py içinde güncelleme
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",  # localhost yerine 0.0.0.0
        port=8002,
        reload=True
    )
```

### 🏢 **5. Şirket Bilgisayarından Erişim**

#### **A) URL Formatı:**
```
Frontend: http://[PC_IP_ADDRESS]:5174
Backend API: http://[PC_IP_ADDRESS]:8002

Örnek:
http://192.168.1.100:5174
```

#### **B) Test Connectivity:**
```bash
# Şirket PC'sinden test
ping 192.168.1.100
telnet 192.168.1.100 5174
telnet 192.168.1.100 8002
```

### 📎 **6. PowerPoint Support Verification**

#### **A) Desteklenen Formatlar:**
- ✅ **PowerPoint**: .pptx, .ppt
- ✅ **Word**: .docx
- ✅ **PDF**: .pdf
- ✅ **Text**: .txt

#### **B) PowerPoint Test:**
1. 5-10 slide'lık bir .pptx dosyası hazırlayın
2. Her slide'da metin content olsun (başlık + içerik)
3. Upload edin ve sistem response'unu kontrol edin

### 🔐 **7. Security Considerations**

#### **A) Sadece Güvenilir Network:**
- Sistemi sadece güvenilir local network'te çalıştırın
- Public internet'e açmayın
- VPN connection üzerinden erişin (gerekirse)

#### **B) CORS Configuration:**
```env
# Sadece şirket IP range'ini allow edin
BACKEND_CORS_ORIGINS=http://192.168.1.*,http://10.0.0.*,http://172.16.*
```

### 🚨 **8. Troubleshooting**

#### **A) Connection Refused:**
- Firewall rules kontrol edin
- PC'nin sleep mode'da olmadığından emin olun
- Antivirus'ün port'ları block etmediğini kontrol edin

#### **B) CORS Errors:**
```bash
# Backend log'larında CORS error varsa
curl -H "Origin: http://COMPANY_PC_IP" http://PC_IP:8002/api/v1/chat/health
```

#### **C) Slow Performance:**
- Network bandwidth kontrol edin
- Large file upload'ları test edin
- Concurrent user limit'ini ayarlayın

### 📊 **9. Performance Monitoring**

#### **A) Network Usage:**
```bash
# Resource Monitor kullanın
resmon
# Network tab → TCP Connections → python.exe/node.exe
```

#### **B) Server Health Check:**
```bash
# Health endpoints
http://PC_IP:8002/api/v1/chat/health
http://PC_IP:8002/api/v1/documents/health
```

### 🎉 **10. Success Verification**

#### **Test Checklist:**
- [ ] PC'den localhost:5174 erişimi çalışıyor
- [ ] Şirket PC'sinden IP:5174 erişimi çalışıyor
- [ ] PowerPoint upload çalışıyor
- [ ] Chat functionality çalışıyor
- [ ] Vector search sonuçlar geliyor
- [ ] Network performance kabul edilebilir

#### **Final URLs:**
```
Your PC (Local): http://localhost:5174
Company Access: http://[YOUR_PC_IP]:5174

Example:
Company Access: http://192.168.1.100:5174
```

---

**🎯 SONUÇ:** Bu konfigürasyon ile hem kendi PC'nizden localhost olarak, hem de şirket ağındaki diğer bilgisayarlardan IP adresi üzerinden sisteme erişebilirsiniz! 