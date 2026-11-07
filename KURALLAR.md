# KURALLAR.md — 10 Katmanlı Analiz Eşikleri ve Uyarı Motoru Yapılandırması

Bu dosya, analiz motorunun her katmanda hangi metriklerde eşik aşıldığında kullanıcıyı uyaracağını tanımlar.
Tüm alanlar opsiyoneldir; boş bırakılanlar devre dışı kalır.

---

## 1. SEKTÖR MAKRO EŞİKLERİ (Katman 1)

```yaml
sektor_makro:
  # Sektör sağlık skoru
  sektor_skoru:
    kritik_alt_esik: 40      # Sektör skoru < 40 → 🔴
    uyarı_esik: 60           # Sektör skoru < 60 → 🟡
  
  # Sektör marj trendi
  marj_trendi:
    daralma_esik_pp: 2.0     # FAVÖK marjı 5 yılda 2 pp+ daralırsa → 🟡
    genisleme_min_pp: 1.0    # FAVÖK marjı 5 yılda 1 pp+ genişlerse → 🟢
  
  # Sektör şok dayanıklılığı
  sok_dayanikliligi:
    marj_dusus_krizde_pp: 5.0    # Krizde marj 5 pp+ düşerse → 🟡
    toparlanma_ay: 18            # Toparlanma > 18 ay → 🔴
  
  # Sektör büyümesi
  ciro_cagr:
    dusuk_esik: 0.05         # 5 yl CAGR < %5 → 🟡
    yuksek_esik: 0.15        # 5 yl CAGR > %15 → 🟢
```

---

## 2. HİKAYE VE STRATEJİ EŞİKLERİ (Katman 2)

```yaml
hikaye_strateji:
  # Yatırım hızı
  yatirim_hizi:
    dusuk_esik_mn_tl_yl: 50      # Yıllık ort. yatırım < 50 Mn TL → 🟡
    yuksek_esik_mn_tl_yl: 500    # Yıllık ort. yatırım > 500 Mn TL → 🟢
  
  # Kendi kaynağı finanse oranı
  oz_kaynak_orani:
    alt_esik: 0.50              # Yatırımların %50'si altı borçla → 🔴
    uyarı_esik: 0.70            # %70 altı borçla → 🟡
  
  # Söz tutarlılığı
  soz_tutarliligi:
    hedef_gerceklesme_orani:
      kritik_alt: 0.50          # Hedeflerin <%50'si gerçekleşirse → 🔴
      uyarı_alt: 0.70           # <%70 → 🟡
  
  # Moat inşası var mı?
  moat_insasi:
    en_az_bir_hendek_turu: true   # En az 1 hendek türü güçlenmiyorsa → 🟡
```

---

## 3. HENDEK (MOAT) EŞİKLERİ (Katman 3)

```yaml
hendek:
  # Hendek skoru (0-100)
  hendek_skoru:
    cok_guclu_alt: 75         # ≥75 → 🟢
    guclu_alt: 50             # 50-74 → 🟡
    orta_alt: 30              # 30-49 → 🟡
    zayif_alt: 30             # <30 → 🔴
  
  # Kriz dayanıklılığı
  kriz_dayanikliligi:
    marj_dusus_krizde_pp: 3.0     # Krizde marj 3 pp+ düşerse → 🟡
    toparlanma_ay: 12             # Toparlanma > 12 ay → 🟡
    pazar_payi_kaybi_krizde_bp: 100   # Krizde pazar payı 100+ bp kaybederse → 🟡
  
  # Fiyatlama gücü
  fiyatlama_gucu:
    maliyet_yansitma_hizi:
      alt_esik: 0.60          # Maliyet artışının <%60'ı fiyata yansıtılırsa → 🟡
      kritik_alt: 0.40        # <%40 → 🔴
  
  # Geçiş maliyeti
  gecis_maliyeti:
    musteri_kaybetme_orani:
      ust_esik: 0.15          # Yıllık müşteri kaybı %>15 → 🟡
      kritik_ust: 0.25        # %>25 → 🔴
  
  # Giriş bariyerleri
  giris_bariyeri:
    sure_yil: 3               # Sektöre giriş > 3 yıl sürüyorsa → 🟢
    sermaye_mn_tl: 500        # Giriş sermayesi > 500 Mn TL → 🟢
```

---

## 4. RAKİP ANALİZİ EŞİKLERİ (Katman 4)

```yaml
rakip:
  # Pazar payı trendi
  pazar_payi:
    kayip_bp_yl: 50           # Yıllık pazar payı > 50 bp kaybederse → 🟡
    kazanim_bp_yl: 50         # Yıllık > 50 bp kazanıyorsa → 🟢
  
  # Maliyet avantajı
  maliyet_avantaji:
    birim_maliyet_farki_pct: 10   # Rakip birim maliyet %10+ düşükse → 🔴
    kazanim: 5                 # Bizim maliyetimiz %5+ düşükse → 🟢
  
  # Karlılık karşılaştırması
  karlilik_vs_rakip:
    roic_farki_pp: 3          # Rakip ROIC bizimkinden 3 pp+ üstündeyse → 🔴
    roe_farki_pp: 5           # Rakip ROE bizimkinden 5 pp+ üstündeyse → 🟡
  
  # Pazar payı kaybı
  pazar_payi_kaybi:
    ard_ard_yl: 2             # Ard arda 2 yıl pazar payı kaybederse → 🔴
```

---

## 5. YÖNETİM / HAKİM ORTAK EŞİKLERİ (Katman 5)

```yaml
yonetim:
  # Söz tutarlılığı
  soz_tutarliligi:
    hedef_gerceklesme_orani:
      kritik_alt: 0.50          # Hedeflerin <%50'si gerçekleşirse → 🔴
      uyarı_alt: 0.70           # <%70 → 🟡
  
  # YK bağımsızlığı
  yk_bagimsizlik:
    bagimsiz_uye_orani:
      kritik_alt: 0.33          # Bağımsız üye oranı <%33 → 🔴 (SPK standardı)
      uyarı_alt: 0.40           # <%40 → 🟡
  
  # Hakim ortak hisse alım/satım
  hakim_ortak_islem:
    net_alim_sinyali:
      net_satim_mn_tl: -10      # Net satım > 10 Mn TL → 🔴
      net_alim_mn_tl: 10        # Net alım > 10 Mn TL → 🟢
  
  # Çıkar çatışması
  cikar_catismasi:
    iliski_taraf_hacim_ciro_orani:
      ust_esik: 0.10            # İlgili taraf işlemleri cironun %>10 → 🔴
      uyarı: 0.05               # %>5 → 🟡
  
  # Yönetim kararlılığı
  kararlilik:
    yk_degisikligi_yl: 2        # Yılda > 2 YK değişikliği → 🟡
    ceo_suresi_yl: 3            # CEO süresi < 3 yıl → 🟡
  
  # Yönetim skoru
  yonetim_skoru:
    guvenilir_alt: 70           # ≥70 → 🟢
    orta_alt: 40                # 40-69 → 🟡
    guvenilmez_alt: 40          # <40 → 🔴
```

---

## 6. SEKTÖR KARŞILAŞTIRMA EŞİKLERİ (Katman 6)

```yaml
sektor_karsilastirma:
  # Marj daralırken/sektör karşılaştırması
  marj_daralma_vs_sektor:
    sektor_daralirken_sirket_ustunde_pp: 1    # Sektör daralırken şirket sektörden 1 pp+ üstündeyse → 🟢
    sektor_daralirken_sirket_altinda_pp: 1    # Sektör daralırken şirket sektörden 1 pp+ altındaysa → 🔴
  
  # Sektör medyanı vs şirket
  vs_sektor_medyan:
    favok_marj_farki_pp: 2      # Şirket FAVÖK marjı sektör medyanından 2 pp+ altındaysa → 🟡
    roe_farki_pp: 3             # ROE sektör medyanından 3 pp altındaysa → 🟡
    roic_farki_pp: 2            # ROIC 2 pp altındaysa → 🟡
    net_borc_favok_kat: 1.5     # Net Borç/FAVÖK sektör medyanının 1.5x'ındaysa → 🔴
  
  # Pazar payı trendi
  pazar_payi:
    sektor_kazanirken_kaybederse: true   # Sektör kazanırken şirket kaybederse → 🔴
    sektor_kaybederken_kazanirsa: true   # Sektör kaybederken şirket kazanıyorsa → 🟢
  
  # Değerleme percentile
  degerleme_percentil:
    kendine_gore_ust_esik: 1.5      # Kendine göre 5 yl percentile > 1.5x → 🔴
    sektore_gore_ust_esik: 1.3      # Sektöre göre > 1.3x → 🟡
```

---

## 7. DUYARLILIK / RİSK EŞİKLERİ (Katman 7)

```yaml
risk:
  # Kırılma noktaları
  kirilma_noktalari:
    cari_oran:
      kritik_alt: 1.0           # Cari < 1.0 → 🔴
      uyarı_alt: 1.2            # Cari < 1.2 → 🟡
    
    net_borc_favok:
      kritik_ust: 5.0           # Net Borç/FAVÖK > 5x → 🔴
      uyarı_ust: 3.0            # > 3x → 🟡
    
    faiz_ortusme:
      kritik_alt: 1.5           # FAVÖK/Faiz < 1.5x → 🔴
      uyarı_alt: 2.0            # < 2.0x → 🟡
    
    nakit_kisa_vadeli_borc:
      kritik_alt: 0.3           # Nakit/Kısa Vadeli Borç < 0.3 → 🔴
      uyarı_alt: 0.5            # < 0.5 → 🟡
    
    ihale_payi:
      kritik_alt: 0.20          # İhale payı <%20 → 🟡 (tek başına risk)
  
  # Duyarlılık katsayıları
  duyarlilik:
    tl_deger_kaybi_20pct:
      favok_etkisi_pp: -10      # TL %20 değer kaybında FAVÖK etki > 10 pp → 🔴
    petrol_95_plus:
      favok_etkisi_pp: -15      # Petrol $95+ etki > 15 pp → 🔴
    faiz_300bp:
      favok_etkisi_pp: -10      # Faiz +300bp etki > 10 pp → 🔴
    kombine_shock:
      favok_etkisi_pp: -25      # Kombine şok etki > 25 pp → 🔴
  
  # Hedge etkinliği
  hedge_etkinligi:
    genel_alt: 0.70             # Genel hedge etkinliği <%70 → 🟡
    kritik_alt: 0.50            # <%50 → 🔴
  
  # İhale bağımlılığı
  ihale_bagimliligi:
    ciro_payi_ust: 0.40         # İhale ciro payı >%40 → 🔴
    tek_ihale_kaybi_etkisi: 0.20  # Tek ihale kaybı ciro etki >%20 → 🔴
```

---

## 8. DEĞERLEME EŞİKLERİ (Katman 8)

```yaml
degerleme:
  # Hendekli şirketler (Moat ≥50)
  hendekli:
    # DCF Güvenlik Marjı
    guvenlik_marji:
      kritik_alt: 10            # <%10 → 🔴
      uyarı_alt: 20             # 10-20% → 🟡
      guclu_alt: 30             # ≥30% → 🟢
    
    # Çarpan Percentile (Kendi 5-10 yl geçmişine göre)
    carpan_percentil:
      pahali_ust: 80            # 5 yl percentile > %80 → 🔴
      pahali_uyari: 60          # >%60 → 🟡
      ucuz_alt: 20              # <%20 → 🟢
    
    # Ters DCF (İçsel Büyüme)
    ters_dcf:
      gecersiz_buyume_ust: 0.05   # İçsel büyüme >%5 (sektörden çok) → 🟡
      sifir_buyume_alt: 0.01      # İçsel büyüme <%1 → 🟡 (piyasa sıfır büyüme fiyatlıyor)
  
  # Hendeksiz şirketler (Moat <50)
  hendeksiz:
    # Kalite kontrol listesi (Tümü 🟢 olmalı)
    kalite_kontrol:
      nc_pozitif: true              # Net Kar > 0
      cfo_gt_nc: true               # CFO/Net Kar > 1.0
      roa_artis: true               # ROA trendi artan
      de_azalma: true               # Borç/Özkaynak trendi azalan
      cari_iyi: true                # Cari ≥ 1.0 ve artan
      sermaye_artirimi_yok: true    # 5 yl sermaye artırımı yok
      brut_marj_artis: true         # Brüt marj trendi artan
      asset_turnover_artis: true    # Asset turnover artan
    
    # Değerleme (Hendeksiz için basit)
    degerleme_yontemi:
      pe_sektor_medyan: true        # P/E sektör medyanı bazlı
      ev_favok_sektor: true         # EV/FAVÖK sektör medyanı
      pb_ozkaynak: true             # P/B özkaynak bazlı
      nakit_temelli: true           # Nakit + 5 yl CFO
    
    # Karar
    karar:
      alinabilir: "Tüm kriterler 🟢 VE fair value > fiyat"
      izle: "1-2 kriter 🔴 VEYA fair value ≈ fiyat"
      kacin: "≥3 kriter 🔴 VEYA fair value < fiyat"
```

---

## 9. BİLANÇO EŞİKLERİ (Katman 9)

```yaml
bilanco:
  # Ciro ve Kâr Büyümesi
  buyume:
    ciro_cagr_5y:
      kritik_alt: 0.03          # 5 yl CAGR <%3 → 🔴
      uyarı_alt: 0.08           # <%8 → 🟡
      guclu_alt: 0.15           # ≥%15 → 🟢
    
    net_kar_cagr_5y:
      kritik_alt: 0.05          # <%5 → 🔴
      uyarı_alt: 0.10           # <%10 → 🟡
      guclu_alt: 0.20           # ≥%20 → 🟢
  
  # Marj Trendi
  marj_trendi:
    favok_marj_dusus_pp:
      uyarı: 2.0                # 5 ylında 2 pp+ daralırsa → 🟡
      kritik: 4.0               # 4 pp+ → 🔴
    
    net_marj_dusus_pp:
      uyarı: 1.5
      kritik: 3.0
    
    diger_faaliyet_gelirleri_payi:
      uyarı: 0.15               # Cironun %>15'i → 🟡
      kritik: 0.25              # %>25 → 🔴
  
  # Borçlanma
  borclanma:
    net_borc_favok:
      kritik_ust: 5.0           # > 5x → 🔴
      uyarı_ust: 3.0            # > 3x → 🟡
      guclu_alt: 1.5            # < 1.5x → 🟢
    
    borc_artisi_yl:
      uyarı: 0.20               # Yıllık %>20 → 🟡
      kritik: 0.50              # %>50 → 🔴
    
    cari_oran:
      kritik_alt: 1.0           # < 1.0 → 🔴
      uyarı_alt: 1.2            # < 1.2 → 🟡
      guclu_alt: 1.5            # ≥1.5 → 🟢
    
    nakit_favok:
      kritik_alt: 0.2           # Nakit/FAVÖK < 0.2 → 🔴
      uyarı_alt: 0.4            # < 0.4 → 🟡
  
  # Nakit Akışı
  nakit_akisi:
    cfo_net_kar_orani:
      alt_esik: 0.8             # CFO/Net Kar < 0.8 → 🟡
      kritik_alt: 0.5           # < 0.5 → 🔴
      guclu_alt: 1.2            # ≥1.2 → 🟢
    
    fcf_net_kar_orani:
      alt_esik: 0.5             # FCF/Net Kar < 0.5 → 🟡
      kritik_alt: 0.0           # Negatif → 🔴
    
    capex_cfo_orani:
      uyarı_ust: 0.80           # Capex/CFO > %80 → 🟡 (Sadece bakım yatırımı)
      kritik_ust: 1.0           # %>100 → 🔴
  
  # KAP Dip Notları
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
      - "tedarikci"
      - "tek tedarikci"
      - "taahhut"
      - "sermaye artirimi"
    her_bulgu_bildir: true
  
  # Kâr Kalitesi
  kar_kalitesi:
    piotroski_f_skoru:
      kritik_alt: 4             # < 4 → 🔴
      uyarı_alt: 6              # < 6 → 🟡
      guclu_alt: 7              # ≥7 → 🟢
    
    beneish_m_skoru:
      kritik_ust: -1.78         # > -1.78 → 🔴
      uyarı_ust: -2.22          # > -2.22 → 🟡
    
    ertelenmis_vergi_payi:
      uyarı_ust: 0.30           # Net kârın %>30'u → 🟡
      kritik_ust: 0.50          # %>50 → 🔴
```

---

## 10. TEKNİK VE POZİSYON EŞİKLERİ (Katman 10)

```yaml
teknik:
  # Trend
  trend:
    ana_trend_yukselen: "SMA50 > SMA200 (Aylık)"     # 🟢
    ana_trend_dusen: "SMA50 < SMA200 (Aylık)"        # 🔴
    trend_guclu_adx: 25                               # ADX > 25 → Güçlü trend
  
  # Momentum
  momentum:
    rsi_asiri_satim: 30       # RSI < 30 → 🟢 (Giriş fırsatı)
    rsi_asiri_alim: 70        # RSI > 70 → 🔴 (Çıkış uyarısı)
    rsi_notr_alt: 40          # RSI < 40 → 🟢 (Giriş bölgesi)
    rsi_notr_ust: 60          # RSI > 60 → 🟡 (Dikkat)
    macd_pozitif: "MACD > Signal"    # 🟢
    macd_negatif: "MACD < Signal"    # 🔴
  
  # Destek/Direnç
  destek_direnc:
    guclu_destek_test_sayisi: 2       # ≥2 test → Güçlü
    guclu_direnc_test_sayisi: 2
    fibonacci_oncelik: [50, 61.8, 38.2, 23.6]  # Öncelik sırası
  
  # Hacim
  hacim:
    ortalama_ustu_katsayi: 1.5      # Hacim 1.5x ortalama üstü → Onay
    dusuk_hacim_kirilim: true       # Düşük hacimle kırılım → 🔴 (Tuzak)
    obv_trend: "Artan"              # OBV artan → 🟢
  
  # Giriş/Çıkış
  giris_cikis:
    rr_min: 1.5                   # Minimum Risk/Ödül 1:1.5
    rr_hedef: 2.5                 # Hedef R/R 1:2.5
    stop_loss_tampon_pct: 2.0     # Destek altı %2-3 tampon
    max_pozisyon_riski: 0.05      # Portföyün %5'i max tek hisse riski
    max_pozisyon_buyuklugu: 0.15  # Portföyün %15'i max tek hisse
    trailing_stop_etkin: true
    trailing_aktivasyon: 0.15     # %15 karıncı trailing aktif
    trailing_mesafe: 0.10         # %10 trailing mesafe
  
  # Pozisyon büyüklüğü
  pozisyon_buyuklugu:
    kelly_kullan: true
    sabit_maksimum: 0.15          # Portföyün max %15'i
    baslangic_pozisyon: 0.35      # Toplam hedefin %30-40'ı başlangıç
    ortalama_alma_bolgeleri: 3    # 3 bölgede toplama
  
  # Fibonacci Öncelik
  fibonacci_oncelik:
    - 50.0
    - 61.8
    - 38.2
    - 23.6
    - 78.6
```

---

## GENEL UYARI MOTORU

```yaml
bildirim:
  kanallar:
    telegram: true
    email: false
    masaustu: false
  
  ozet_gonderim_saatleri:
    - "08:30"
    - "19:00"
  
  gecmis_bildirim_suresi_gun: 30
  ayni_bildirim_tekrar_saat: 4
  
  # Kural ihlali bildirimi
  kural_ihlali_bildirimi:
    sektor_skoru_dusuk: true
    hendek_zayif: true
    yonetim_guvenilmez: true
    degerleme_pahali: true
    bilanco_zayif: true
    tekniks_giris_uygun_degil: true
    risk_kritik: true
```

---

**Not:** Bu dosya proje kökünde (`KURALLAR.md`) tutulur. Analiz motoru her çalıştığında bu dosyayı okur ve eşikleri uygular. Değişiklikler anlık yansır (yeniden başlatma gerekmez).