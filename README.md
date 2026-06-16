# Social Diff

**Türkçe**    [English](README.md) · 

Instagram ve Twitter/X için takipçi–takip karşılaştırması yapıp **iki yönlü
eşleşmeme** listesi çıkarır:

- **Don't follow you back** — sen takip ediyorsun, o seni geri takip etmiyor.
- **You don't follow back** — o seni takip ediyor, sen onu takip etmiyorsun.

## Nasıl çalışır?

1. Açılışta iki büyük buton görürsün: **Instagram** ve **Twitter / X**. Birine
   tıklayınca o platformun ekranı açılır.
2. Kullanıcı adını yaz, **"Open browser"**'a bas → bir Chrome penceresi açılır,
   **giriş'i sen yaparsın** (2FA / checkpoint dahil, süre sınırı yok).
3. **"I'm logged in → Fetch lists"**'e bas → script profilini gezip takipçi/takip
   listelerini kaydırarak toplar, karşılaştırır, sonucu ekranda gösterir ve
   `.txt` dosyalarına kaydeder.
4. İstediğin an **"Stop"** (veya **"Back"**) ile işlemi durdurabilirsin; bu Chrome
   penceresini de kapatır.

Giriş bilgisi yerel `chrome-profile/` klasöründe saklanır, böylece bir sonraki
sefer zaten giriş yapmış olursun.

## İndirme

```bash
git clone https://github.com/hgunduzoglu/social-diff.git
```

veya GitHub arayüzünden **Download ZIP** ile indirip aç.

## Gereksinimler

- **Google Chrome** (ya da Chromium) kurulu olmalı — sürücüyü Selenium otomatik indirir.
- **Python 3** (Tk 8.6+ ile). Launcher'lar ilk açılışta kendi sanal ortamını kurup
  Selenium'u otomatik yükler.

## Çalıştırma

| İşletim sistemi | Yapılacak |
|-----------------|-----------|
| **macOS** | `run.command` dosyasına çift tıkla. Tk'li Python yoksa: `brew install python-tk` |
| **Windows** | `run.bat` dosyasına çift tıkla |
| **Linux** | Terminalde `./run.sh` (önce `chmod +x run.sh`). Gerekirse: `sudo apt install python3-venv python3-tk` |

## Tek dosyalık uygulama (isteğe bağlı)

- **Windows .exe:** `build_windows.bat` çalıştır → `dist\SocialDiff\SocialDiff.exe`
- **macOS .app:** `build_mac.command` çalıştır → `dist/SocialDiff.app`

## Dosyalar

| dosya | amaç |
|-------|------|
| `app.py` | arayüz (GUI) |
| `scrape.py` | Selenium toplayıcı (CLI olarak da çalışır) |
| `compare.py` | karşılaştırma mantığı (CLI olarak da çalışır) |
| `run.command` / `run.bat` / `run.sh` | başlatıcılar (macOS / Windows / Linux) |
| `build_windows.bat` / `build_mac.command` | tek dosyalık uygulama üret |

## Komut satırı (isteğe bağlı)

```bash
python scrape.py instagram KULLANICI_ADIN
python scrape.py twitter   KULLANICI_ADIN
python compare.py --following-list instagram_following.txt \
                  --followers-list instagram_followers.txt \
                  --platform Instagram --save result_instagram
```

## Notlar

- Sosyal medya kazımak sitelerin kullanım şartlarına aykırıdır; kendi hesabınla,
  riskini bilerek kullan ve arka arkaya çok çalıştırma (rate limit).
- Site HTML'i değişirse `scrape.py` içindeki CSS seçicileri güncellemen gerekebilir.
