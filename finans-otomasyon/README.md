# Finans Otomasyon Projesi 📈

BIST takip + analiz otomasyonu. Kullanicinin PC'si KAPALIYKEN bile calisir
(GitHub Actions bulut sunucusunda calisir).

## Ne yapar?

1. Takip listesindeki hisselerin fiyat verisini ceker (Yahoo Finance)
2. GLM 5.3 Flash (NVIDIA ucretsiz erisim) ile Turkce ozet yazdirir
3. Telegram'dan telefona gonderir

## Zamanlama

- Sabah 08:30 (hafta ici) — gecenin/bugunun acilis oncesi durumu
- Aksam 19:00 (hafta ici) — gunun kapanis ozeti

## Kurulum (bir kez yapilir)

Gerekli GitHub secrets (repo ayarlarindan, Settings → Secrets and variables → Actions):

| Secret | Aciklama |
|---|---|
| NVIDIA_API_KEY | build.nvidia.com'dan alinan anahtar (opencode.json icindekini de kullanabilir) |
| TELEGRAM_BOT_TOKEN | @BotFather'dan alinan bot token'i |
| TELEGRAM_CHAT_ID | Kullanicinin Telegram chat ID'si (bota ilk mesaj atinca ogrenilir) |
| WATCHLIST | Virgulle ayri hisse listesi, orn: ASELS.IS,THYAO.IS |
| MODEL | Kullanilacak model, orn: z-ai/glm-5.3-flash |

## Dosyalar

- `scripts/gunluk_ozet.py` — ana script (fiyat + analiz + Telegram)
- `.github/workflows/ozet.yml` — zamanlanmis gorev tanimi

## Onemli notlar

- Bu sistem **bilgi verir**, yatirim tavsiyesi vermez.
- GitHub Actions ucretsiz kotasi: ayda ~2000 dakika; bu sistem ayda ~60 dakika harcar.
- GitHub, 60 gun hic aktivite olmayan repolarda zamanlanmis gorevleri durdurur —
  arada bir repoya "el ile calistir" (workflow_dispatch) demek yeterli.

## Yol haritasi (siradaki adimlar)

- [ ] Faz 1: Telegram bot + GitHub repo + secrets kurulumu
- [ ] Faz 1: Ilk gunluk ozet gonderimi
- [ ] Faz 2: KAP bildirim entegrasyonu (API semasi arastirilacak)
- [ ] Faz 2: Bilanco verisi (kar, FAVOK, marjlar, 5-10 yil) — /analiz raporu
- [ ] Faz 2: Hendek testi + rakip analizi raporu (ASELS ile ilk ornek)
- [ ] Faz 3: KAP dip not tarayici ("kullanicinin kacirdiklari")
