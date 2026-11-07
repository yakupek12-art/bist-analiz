with open('layers.py', 'w', encoding='utf-8') as f:
    f.write('''# -*- coding: utf-8 -*-
"""
Katman tanimlari - OpenCode agent'siz, NVIDIA API direct
Tum karakterler ASCII guvenli
"""

layers = [
    {
        "name": "sektor-ajani",
        "desc": "Katman 1: Sektor Makro",
        "files": "veri/sektor_veri.json veri/sektor_peerler.txt veri/makro_veri.json",
        "system": "Sen BIST sektor analistisin. Verilen sektor verilerini, peer medyanlarini, makro verileri analiz et. Cikti: Markdown rapor (Tablo + Anlatim). Sadece rapor yaz, aciklama yapma.",
        "user_template": """Asagidaki verileri analiz et ve sektor makro raporu yaz:

=== SEKTOR VERISI ===
{sektor_veri}

=== PEER LISTESI ===
{sektor_peerler}

=== MAKRO VERISI ===
{makro_veri}

Cikti formati:
## KATMAN 1: SEKTOR MAKRO ANALIZI

### TABLO: SEKTOR 5 YIL OZET
| Yil | Sektor Ciro | YoY % | FAVOK Marj % | Net Marj % | Peer Medyan P/E | Para Akisi |
|-----|-------------|-------|--------------|------------|-----------------|------------|

### SEKTOR TREND ANALIZI
- Ciro Trendi: ...
- Marj Trendi: ...
- Karlilik Kalitesi: ...
- Para Akisi: ...

### SOK DAYANIKLILIGI
- 2020-2024 arasi tepkiler...
- Marj dayanikligli...
- Borclanma dayanikligli...

### SEKTOR SAGLIK SKORU (0-100)
- Ciro Buyumesi: X/20
- Marj Trendi: X/20
- Karlilik: X/20
- Sok Dayanikligiligi: X/20
- Degerleme Cazibesi: X/20
- TOPLAM: X/100

### SEKTOR KARARI
[SAGLIKLI] / [ORTA] / [HASTALIKLI]
Gercekce: ..."""
        },
        {
            "name": "hikaye-ajani",
            "desc": "Katman 2: Hikaye & Strateji",
            "files": "veri/hikaye_veri.json veri/bilanco.csv veri/kap_yatirim_planlari.txt",
            "system": "Sen BIST sirket hikayesi analistisin. Sirketin kimligini, asil para kaynagini, gelecek yatirimlarini, kapasite genisletme planlarini analiz et. Cikti: Markdown rapor (Tablo + Anlatim).",
            "user_template": """Asagidaki verilerle sirket hikayesini cikar:

=== HIKAYE VERISI ===
{hikaye_veri}

=== BILANCO OZET ===
{bilanco_ozet}

=== YATIRIM PLANLARI (KAP) ===
{kap_yatirim_planlari}

Cikti formati:
## KATMAN 2: SIRKET HIKAYESI VE STRATEJI

### SIRKET KIMLIGI
- Kurulus, sahip yapisi, ana faaliyet, pazar konumu

### ASIL PARA KAYNAGI
| Segment | Pay %% | 5 Yl Trendi | Marj %% |

### GELECEK YATIRIMLAR VE KAPASITE
| Proje | Butce | Bitis | Beklenti | Kaynak |

### MOAT INSASI
| Moat Turu | Var mi? | Guc (1-10) | Kanit |

### HIKAYE KARARI
[GUCLU] / [ORTA] / [ZAYIF]
Gercekce: ..."""
        },
        {
            "name": "hendek-ajani",
            "desc": "Katman 3: Hendek (Moat) - 5/10 Yil",
            "files": "veri/hendek_veri.json veri/rakip_giris_bariyerleri.txt veri/kriz_performans.txt",
            "system": "Sen hendek (moat) analistisin. 5-10 yil veriyle fiyatlama gucu, kriz dayanikligiligi, ag etkisi, gecis maliyeti, rakip giris bariyerlerini analiz et. Cikti: Markdown rapor (Tablo + Skorlama 0-100).",
            "user_template": """Asagidaki verilerle hendek analizi yap:

=== HENDEK VERISI ===
{hendek_veri}

=== RAKIP GIRIS BARIYERLERI ===
{rakip_giris_bariyerleri}

=== KRIZ PERFORMANSI ===
{kriz_performans}

Cikti formati:
## KATMAN 3: HENDEK (MOAT) ANALIZI -- 5/10 YIL

### TABLO: HENDEK METRIKLERI 5/10 YIL
| Yil | Brut Marj %% | FAVOK Marj %% | Net Marj %% | Pazar Payi %% | Fiyatlama Gucu | Gecis Maliyeti |
|-----|-------------|--------------|------------|--------------|----------------|----------------|

### HENDEK TURLERI VE GUCLUGU (0-10)
| Hendek Turu | Var mi? | Guc (0-10) | 5 Yl Trendi | Kanit |
|-------------|---------|------------|-------------|-------|

### KRIZ DAYANIKLILIGI
| Kriz | Marj Degisimi | Pazar Payi | Toparlanma | Not |

### HENDEK SKORU (0-100)
| Bilesen | Skor | Agirlik | Agirlikli |

### HENDEK KARARI
[COK GUCLU] / [GUCLU] / [ORTA] / [ZAYIF]
Gercekce: ..."""
        },
        {
            "name": "rakip-ajani",
            "desc": "Katman 4: Rakip Derin Analizi",
            "files": "veri/rakip_veri.json veri/rakip_karsilastirma.json veri/sektor_veri.json",
            "system": "Sen rakip analistisin. Secili rakipleri derin analiz et: 5-10 yl karlilik, urun farklastirmasi, maliyet avantaji, pazar payi trendi. Cikti: Markdown rapor (Karsilastirma tablolari + Tehdit matrisi).",
            "user_template": """Rakip analizi verileri:

=== RAKIP VERISI ===
{rakip_veri}

=== RAKIP KARSILASTIRMA ===
{rakip_karsilastirma}

=== SEKTOR VERISI ===
{sektor_veri}

Cikti formati:
## KATMAN 4: RAKIP DERIN ANALIZI

### SECILI RAKIP LISTESI
| Rakip | Kod | Secim Nedeni | Pazar Payi %% | Benzerlik %% |

### KARSILASTIRMA TABLOSU (5 YIL)
| Metrik | Bizim Sirket | Rakip A | Rakip B | Sektor Medyan | Siralama |

### MALIYET AVANTAJI KARSILASTIRMASI
| Maliyet Kalemi | Bizim | Rakip A | Sektor Ort. | Avantaj |

### PAZAR PAYI TRENDI (5 YIL)
| Yil | Bizim %% | Rakip A %% | Rakip B %% | Toplam Pazar |

### RAKIP TEHDIT MATRISI
| Rakip | Tehdit | Neden | Tehdit Turu | Cevap |

### RAKIP KARARI
[GUCLU POZISYON] / [ORTA] / [ZAYIF] / [KAYBEDILIYOR]
Gercekce: ..."""
        },
        {
            "name": "yonetim-ajani",
            "desc": "Katman 5: Yonetim / Hakim Ortak Guvenilirligi",
            "files": "veri/yonetim_veri.json",
            "system": "Sen yonetim kalitesi analistisin. Hakim ortak profili, YK bagimsizligi, soz tutarliligi, hisse alim/satim, cikar catismalari analiz et. Cikti: Markdown rapor (Profil tablolari + Skorlama 0-100).",
            "user_template": """Yonetim verileri:

=== YONETIM VERISI ===
{yonetim_veri}

Cikti formati:
## KATMAN 5: YONETIM / HAKIM ORTAK GUVENILIRLIGI

### HAKIM ORTAK PROFILI
| Ozellik | Deger | Degerlendirme |

### YK BAGIMSIZLIGI
| Uye | Rol | Bagimsiz? | Sektor Deneyimi | Cikar Catismasi |

### SOZ TUTARLILIGI (5-10 YIL)
| Yil | Hedef | Gerceklesme | Tutarlilik |

### HAKIM ORTAK ALIM/SATIM
| Tarih | Islem | Adet | Fiyat | Anlam |

### YONETIM GUVENILIRLIK SKORU (0-100)
| Bilesen | Skor | Agirlik | Agirlikli |

### YONETIM KARARI
[GUVENILIR] / [ORTA] / [GUVENILMEZ]
Gercekce: ..."""
        },
        {
            "name": "sektor-karsilastirma-ajani",
            "desc": "Katman 6: Sektor Ortalamasi vs Sirket",
            "files": "veri/sektor_karsilastirma.json veri/sektor_veri.json veri/finansal_derinlik.json",
            "system": "Sen sektor karsilastirma analistisin. Sirketi sektor medyan/ortalamasi ve en iyi/kotu peerlerle karsilastir. Marjlar, karlilik, degerleme, pazar payi. Cikti: Markdown rapor (Tablo + Karsilastirma + Karar).",
            "user_template": """Karsilastirma verileri:

=== SEKTOR KARSILASTIRMA ===
{sektor_karsilastirma}

=== SEKTOR VERISI ===
{sektor_veri}

=== FINANSAL DERINLIK ===
{finansal_derinlik}

Cikti formati:
## KATMAN 6: SEKTOR ORTALAMASI vs SIRKET

### TABLO: SEKTOR vs SIRKET -- 5 YIL ORTALAMALAR
| Metrik | Sirket | Sektor Medyan | Sektor Ort. | En Iyi Peer | Siralama |

### MARJ DARALIRKEN/ GENISLERKEN KARSILASTIRMA
| Donem | Sektor FAVOK Marj D | Sirket FAVOK Marj D | Fark | Yorum |

### SEKTOR KARSILASTIRMA KARARI
[SEKTOR USTU] / [PARITE] / [SEKTOR ALTI]
Gercekce: ..."""
        },
        {
            "name": "risk-ajani",
            "desc": "Katman 7: Duyarlilik ve Risk Analizi",
            "files": "veri/duyarlilik_veri.json veri/makro_veri.json veri/ihale_bagimliligi.txt veri/kredi_kosullari.txt",
            "system": "Sen risk analistisin. Sirketin duyarlilik katsayilarini (FX, petrol, faiz, ihale), hedge etkinligi, makro sok senaryolari, kirilma noktalari, ihale/kredi riskini analiz et. Cikti: Markdown rapor (Duyarlilik tablosu + Sok senaryolari + Kirilma noktalari).",
            "user_template": """Risk verileri:

=== DUYARLILIK VERISI ===
{duyarlilik_veri}

=== MAKRO VERI ===
{makro_veri}

=== IHALE BAGIMLILIGI ===
{ihale_bagimliligi}

=== KREDI KOSULLARI ===
{kredi_kosullari}

Cikti formati:
## KATMAN 7: DUYARLILIK VE RISK ANALIZI

### DUYARLILIK KATSAYILARI
| Risk Faktoru | Katsayi | Anlam |

### HEDGE PROGRAMI
| Risk | Oran %% | Arac | Vade | Etkinlik %% | Acik Pozisyon |

### MAKRO SOK SENARYOLARI
| Sok | Ciro Etkisi | FAVOK Etkisi | Net Kar Etkisi | Cari Etkisi | Dayaniklik |

### KIRILMA NOKTALARI
| Risk | Esik | Mevcut | Mesafe | Olasilik |

### RISK KARARI
[DUSUK] / [ORTA] / [YUKSEK] / [KRITIK]
En Buyuk 3 Risk: 1) ... 2) ... 3) ...
Kirilma Noktasi: ..."""
        },
        {
            "name": "degerleme-ajani",
            "desc": "Katman 8: Degerleme (Hendekli vs Hendeksiz)",
            "files": "veri/degerleme_girdi.json veri/finansal_derinlik.json veri/hendek_skor.json",
            "system": "Sen degerleme analistisin. Hendek durumuna gore dogru yontemi uygula: Hendekliyse DCF/Carpan Percentile/Ters DCF/Guvenlik Marji; Hendeksizse NC>0, CFO>NC, ROA artis, Borc/Ozkaynak dusus, Cari dusus, Sermaye artirimi yok, Marj artisi, Asset turnover artisi. Cikti: Markdown rapor (DCF tablosu + Percentile + Ters DCF + Karar).",
            "user_template": """Degerleme verileri:

=== DEGERLEME GIRDISI ===
{degerleme_girdi}

=== FINANSAL DERINLIK ===
{finansal_derinlik}

=== HENDEK SKORU ===
{hendek_skor}

Cikti formati:
## KATMAN 8: DEGERLEME

### HENDEK DURUMU
Hendek Skoru: X/100 -> HENDEKLI (>=50) / HENDEKSIZ (<50)

### A) HENDEKLI ICIN DEGERLEME
#### DCF (3 SENARYO)
| Senaryo | WACC | g | Fair Value | Hisse Bazinda | Guvenlik Marji |

#### CARPAN PERSENTIL (5-10 YIL)
| Carpan | Mevcut | 5 Yl Medyan | Percentil | Sektor vs Sirket |

#### TERS DCF
- Icsel Buyume: X%% | Sektor: Y%% -> Piyasa neyi fiyatliyor?

#### GUVENLIK MARJI
- Baz Fair Value: X TL | Mevcut: Y TL | Marj: Z%%

### B) HENDEKSIZ ISE
#### KALITE KONTROL LISTESI
| Kriter | Esik | Mevcut | Sonuc |

### DEGERLEME KARARI
[ALINABILIR] / [IZLE] / [KACIN]
Gercekce: ..."""
        },
        {
            "name": "bilanco-ajani",
            "desc": "Katman 9: Bilanco Derin Okuma (5-10 Yil)",
            "files": "veri/bilanco.csv veri/finansal_derinlik.json veri/kap_dip_notlari.txt",
            "system": "Sen bilanco analistisin. 5-10 yillik bilanco/gelir/nakit akim tablosunu derinlemesine oku. Yillik tablolar + anlatim: Ciro->Net Kar, Marjlar, Borc, Nakit Akisi, Oranlar, KAP dip notlari. 'Ne anliyorum?' anlatimi. Cikti: Markdown rapor (6 Tablo + Anlatim + Karar).",
            "user_template": """Bilanco verileri:

=== BILANCO CSV ===
{bilanco_csv}

=== FINANSAL DERINLIK ===
{finansal_derinlik}

=== KAP DIP NOTLARI ===
{kap_dip_notlari}

Cikti formati:
## KATMAN 9: BILANCO DERIN OKUMA (5-10 YIL)

### TABLO 1: CIRO -> NET KAR (5-10 YIL)
| Yil | Ciro | YoY D%% | Brut Kar | Brut Marj %% | Esas Faaliyet K | Faaliyet Marj %% | FAVOK | FAVOK Marj %% | Net Kar | Net Marj %% | YoY D%% |

### TABLO 2: MARJ TRENDI (5 YIL)
| Yil | Brut Marj %% | Esas Faaliyet Marj %% | FAVOK Marj %% | Net Marj %% | Diger Faaliyet Gelirleri / Ciro %% |

### TABLO 3: BORCLANMA VE LIKIDITE (5 YIL, Mn TL)
| Yil | Kisa Vadeli Borc | Uzun Vadeli Borc | Toplam Fin. Borc | Nakit | Net Borc | Net Borc/FAVOK | Cari Oran | Nakit/FAVOK |

### TABLO 4: NAKIT AKISI (5 YIL, Mn TL)
| Yil | CFO | Capex | FCF | FCF/Net Kar | FCF Marj %% | Temettu | Sermaye Artirimi | Borclanma (Net) |

### TABLO 5: ONEMLI ORANLAR (5 YIL)
| Oran | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Trendi | Sektor Medyan |

### TABLO 6: KAP DIP NOTLARI (Kritik Bulgular)
| # | Dip Not Konusu | Yil | Ozet | Mali Etki | Risk |

### BILANCO ANALITIMI (Ne Anliyorum?)
> [3-5 paragraf: Ciro/Kar trendi, Marj nedenleri, Borc/Nakit durumu, Kritik bulgu]

### BILANCO KARARI
[SAGLIKLI] / [ORTA] / [ZAYIF]
Gercekce: ..."""
        },
        {
            "name": "teknik-ajani",
            "desc": "Katman 10: Teknik Analiz ve Pozisyon Belirleme",
            "files": "veri/teknik.json veri/fiyat.json veri/hacim_profili.json",
            "system": "Sen teknik analistisin. Uzun vadeli value investing icin giris/cikis seviyeleri, pozisyon buyuklugu, stop-loss, R/R, Fibonacci, hacim profili. Cikti: Markdown rapor (Trend + Destek/Direnç + Giris/Cikis bolgeleri + Stop/R/R + Kelly).",
            "user_template": """Teknik veriler:

=== TEKNIK VERILER ===
{teknik_veri}

=== FIYAT VERISI ===
{fiyat_veri}

=== HACIM PROFILI ===
{hacim_profili}

Cikti formati:
## KATMAN 10: TEKNIK ANALIZ VE POZISYON BELIRLEME

### TREND ANALIZI (Coklu Zaman Dilimi)
| Zaman Dilimi | Trend | SMA50 vs SMA200 | MACD | ADX |

### DESTEK VE DIRENC SEVIYELERI
| Seviye | Tip | Fiyat | Gucluk | Test Sayisi |

### MOMENTUM INDIKATORLERI
| Indikator | Deger | Sinyal |

### FIBONACCI RETRACEMENT / EXTENSION
| Seviye | Fiyat | Tip |

### GIRIS / CIKIS STRATEJISI (UZUN VADHELI VALUE INVESTING)
| Bolge | Fiyat Araligi | Pozisyon %% | Sebep | Oncelik |

### CIKIS SEVIYELERI (Sell Zones)
| Bolge | Fiyat Araligi | Pozisyon %% | Sebep |

### STOP-LOSS VE RISK YONETIMI
| Parametre | Deger | Hesaplama |

### POZISYON YONETIMI KURALLARI
1. Baslangic Pozisyonu: Toplam hedefin %%30-40'i (Bolge 1-2'de)
2. Ortalama Alma: Fiyat duserse Bolge 2-3'te toplama yap, maliyeti dusur
3. Kismi Kar Alimi: Direnc seviyelerinde %%20-30'ar kar al
4. Stop Loss: Gunluk kapanis Destek 1 altinda kalirsa tam cikis
5. Trailing Stop: Kar +15%% ulasirsa stop'u maliyete cek, +30%% ulasarsa %%10 trailing
6. Maksimum Bekleme: 18-24 ay (Value investing horizonti)

### TEKNIK KARARI
[GIRIS UYGUN] / [BEKLE] / [GIRIS ERTELE]
Giris Onceligi: X/10 | Stop: X | Hedef 1: X (R/R 1:X) | Hedef 2: X (R/R 1:X)"
        }
    ]
''')
print('layers.py written successfully')