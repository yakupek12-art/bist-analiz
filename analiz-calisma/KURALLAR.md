# KURALLAR.md — Kullanıcı Eşikleri ve Uyarı Motoru Yapılandırması

Bu dosya, analiz motorunun hangi metriklerde eşik aşıldığında kullanıcıyı uyaracağını tanımlar.
Tüm alanlar opsiyoneldir; boş bırakılanlar devre dışı kalır.

## 1. FİYAT / TEKNİK EŞİKLER

```yaml
fiyat:
  # Yüzde değişim eşikleri (günlük/haftalık/aylık)
  gunluk_degisim_ust: 5.0      # Günlük +%5 üzeri -> uyarı
  gunluk_degisim_alt: -5.0     # Günlük -%5 altı -> uyarı
  haftalik_degisim_ust: 15.0
  haftalik_degisim_alt: -15.0
  aylik_degisim_ust: 30.0
  aylik_degisim_alt: -25.0

  # Hareketli ortalama kırılımları
  ma_kirilim:
    ma20_ustunde_kapanma: true    # Fiyat MA20'nin üzerine kapanırsa
    ma20_altina_kapanma: true     # Fiyat MA20'nin altına kapanırsa
    ma50_ustunde_kapanma: true
    ma50_altina_kapanma: true
    ma200_altina_kapanma: true    # Uzun vadeli trend kırılımı (kritik)

  # RSI eşikleri
  rsi:
    asiri_alim: 70
    asiri_satim: 30
    cizgi_70_ustu_kirilma: true
    cizgi_30_alti_kirilma: true

  # Hacim
  hacim:
    ortalama_ustu_katsayi: 2.0    # Günlük hacim 2x ortalama üstü
    dusuk_hacim_azalma: 0.5       # Hacim ortalamanın yarısına düşerse
```

## 2. TEMEL / FİNANSAL EŞİKLER

```yaml
temel:
  # Marj düşüşü
  faaliyet_marj_dusus:
    esik_yuzde: 3.0          # Faaliyet marjı 3 pp'den fazla düşerse
    sure_ceyrek: 2           # Ard arda 2 çeyrek

  net_marj_dusus:
    esik_yuzde: 2.0
    sure_ceyrek: 2

  # Borçlanma
  net_borc_favok:
    ust_esik: 3.0            # Net Borç / FAVOK > 3x
    kritik_esik: 5.0         # > 5x kritik

  cari_oran:
    alt_esik: 1.2            # Cari oran < 1.2 riskli
    kritik_alt: 1.0

  # Borç artışı
  finansal_borc_artisi:
    ceyrek_ceyrike_yuzde: 20 # Çeyrekte %20'den fazla artış
    yillik_yuzde: 50

  # Nakit pozisyonu
  nakit_azalma:
    ceyrek_ceyrike_yuzde: 30
    minimum_nakit_favok: 0.2 # Nakit / FAVOK < 0.2 riskli
```

## 3. KÂR KALİTESİ EŞİKLERİ

```yaml
kar_kalitesi:
  # Normalize kâr marjı
  normalize_kar_marj_dusus:
    esik_pp: 2.0             # Normalize kâr marjı 2 pp düşerse

  # CFO / Net Kar
  cfo_net_kar_orani:
    alt_esik: 0.8            # CFO / Net Kar < 0.8 şüpheli
    kritik_alt: 0.5

  # Ertelenmiş vergi payı
  ertelenmis_vergi_payi:
    ust_esik: 30             # Net kârın %30'u ertelenmiş vergiden geliyorsa

  diger_faaliyet_gelirleri_payi:
    ust_esik: 20             # Diğer faaliyet gelirleri / Satış > %20
```

## 4. DEĞERLEME EŞİKLERİ

```yaml
degerleme:
  # F/K çarpanı
  f_k:
    sektor_ort_ustu_katsayi: 1.3    # Sektör ortalamasının 1.3x'i üzeri pahalı
    kendine_gore_ust_esik: 1.5      # Kendi 5 yl ortalamasının 1.5x'i

  pd_dd:
    ust_esik: 3.0

  # DCF güvenlik marjı
  guvenlik_marji:
    alt_esik: 20              # Güvenlik marjı <%20 riskli
    kritik_alt: 10
```

## 5. HABER / GÜNDEM EŞİKLERİ

```yaml
haber:
  onem_skoru:
    kritik_esik: 4           # Skor >= 4 anında bildirim
    onemli_esik: 3           # Skor >= 3 günlük özetine al

  kaynak_guvenilirlik:
    guvenilir_kaynaklar: ["kap.org.tr", "paratic.com", "hisse.net", "finanshatti.com"]
    dusuk_guvenilirlik: ["tradingview.com", "forum", "twitter"]
```

## 6. KAP / DİP NOT EŞİKLERİ

```yaml
kap_dip_notlari:
  kritik_anahtarlar:
    - "teminat"
    - "rehin"
    - "ipotek"
    - "dava"
    - "ilgili taraf"
    - "kambiyo"
    - "hedge"
    - "müşteri yoğun"
    - "tek müşteri"
    - "ertelenmis vergi"
    - "diger faaliyet gelirl"
    - "faaliyet karina diger gelirlere bagli"
    - "tedarikci"
    - "tek tedarikci"
  her_bulgu_bildir: true
```

## 7. BİLDİRİM AYARLARI

```yaml
bildirim:
  kanallar:
    telegram: true
    email: false
    masaustu: false

  ozet_gonderim_saatleri:
    - "08:30"   # Sabah
    - "19:00"   # Akşam

  gecmis_bildirim_suresi_gun: 30   # 30 günlük geçmiş tut
  ayni_bildirim_tekrar_saat: 4     # Aynı uyarı 4 saatte bir tekrar edilmez
```

---

**Not:** Bu dosya `analiz-calisma/KURALLAR.md` konumunda tutulur. Analiz motoru her çalıştığında bu dosyayı okur ve eşikleri uygular. Değişiklikler anlık yansır (yeniden başlatma gerekmez).