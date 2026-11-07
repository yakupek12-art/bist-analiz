# ASELS — Ayı (Red-Team) Analizi (ayi-ajani, 27 Ekim 2026)

*Araç kullanılmadı. Verilen bilânço bulguları + haber başlıkları temel alındı; doğrulanamayanlara "kanıt yetersiz" etiketi kondu.*

## EN GÜÇLÜ 3 RİSK

### 1️⃣ Nakit üretmeyen büyüme: stok–alacak girdabı — Olasılık: YÜKSEK | Etki: ORTA-YÜKSEK
Net borç 6 ayda ikiye katlanmış, cari oran ~1,1'de sıkışık, kur çevrim farkları nakit yiyor. Üstelik yeni açıklanan milyarlarca euroluk sözleşmeler **gelir değil, önce sermaye ihtiyacıdır**: savunma tahsilatları uzun vadeli — sipariş defteri ne kadar hızlı şişerse nakit açığı o kadar hızlı büyür. Kâr artarken serbest nakit akışı zayıf kalırsa büyüme ya ek borçla ya seyreltici sermaye artırımıyla finanse edilir. Hikâyenin en kırılgan ekleği.

### 2️⃣ Kâr kalitesi: başlıkta +%75, marj ise eriyor — Olasılık: ORTA-YÜKSEK | Etki: YÜKSEK
Haberler "9 aylık net kâr %75 arttı" derken faaliyet marjı 32,5%'ten 25,5%'e düşmüş ve 2024 net kârının ~%45'i ertelenmiş vergi kaynaklı. Ertelenmiş vergi nakit yaratmaz. Marj düşerken net kârın sıçraması, kârın hasılattan değil tahakkuktan/nakit-dışı kalemlerden geldiğinin klasik işareti. Piyasa bunu geç fark ederse düzeltme sert olur. FAVÖK %20 eşiği henüz ihlal değil ama **yön aşağı** — KURALLAR.md takibi şart.

### 3️⃣ Pahalı hikâye + kurumsal dağıtım sinyali — Olasılık: ORTA | Etki: ORTA-YÜKSEK
BofA'nın 1,5 milyar TL'lik blok satışı (23 Eki), konsensüs coşkusu içinde (hedef 517,20 TL) ilk büyük kurumsal çıkış sinyali. Güncel P/E ve P/FAVÖK elimizde yok (kanıt yetersiz); ancak "savunma lideri" primiyle fiyatlanan hissede tek bir marj şaşkınlığı birden çok çarpan düzeltmesini tetikleyebilir.

## İZLEME LİSTESİ (kısa)
- **Kur (%20 senaryosu):** Döviz yükümlülük çevrim kayıpları büyür; tahsilat gecikmesi kazancı 6-12 ay öteler. Net korunma durumu: **kanıt yetersiz** (27 Eki Faaliyet Raporu'ndan doğrulanmalı).
- **Müşteri yoğunluğu:** Kamu alıcısı + ihracat bağımlılığı; somut oran **kanıt yetersiz**.
- **Regülasyon:** İhracat lisansı/müttefik denetim baskısı, kamu sözleşmelerinde fiyat endeksleme gecikmeleri — **kanıt yetersiz**.
- **Rekabet:** Thales, Leonardo, Rohde & Schwarz, Hanwha sınıfı uluslararası oyuncular + yerli ekosistem pay artışı marj baskısı yapabilir (yorum — veri yok).
- **Geçmiş davranış:** Sermaye artırım/taahhüt ihlali geçmişi doğrulanamadı — **kanıt yetersiz**; Risk 1'deki fonlama ihtiyacı ilk kez seyreltme tartışması kapısını aralayabilir.

## 🕳️ BU HİKÂYE NEREDEN ÇÖKER?
Nakit–kalite kesişiminde: milyarlarca euroluk sözleşmeler sipariş defterini patlatır; ama savunmada her yeni kâr birimi daha çok stok + daha uzun alacak demek → serbest nakit akışı negatif kalır, 6 ayda ikiye katlanan net borç daha da ileri gider, cari oran 1,1'in altına sarkar. Aynı anda maliyet baskısı marjı 25,5%'in altına sürer; piyasa kârın önemli bölümünün nakit-dışı kalemlerden geldiğini fark eder. Kur farkları nakdi yemeye devam ederken şirket ya pahalı borçlanır ya sermaye artırımı gündeme gelir — seyreltme korkusu "savunma lideri" çarpanlarını ezer. BofA blok satışı bu dönüşün davul sesi olabilir: hikâye "büyüme"den "nakit akışı nerede?" sorusuna döndüğü an fiyat, kâra değil **nakit açığına** göre yeniden fiyatlanır.

## KAYNAKLAR
1. Bilânço analisti bulguları (2026 H1: net borç 2x, marj gerilemesi, stoklar, ertelenmiş vergi, cari ~1,1)
2. Paratic 26.10 — 9M kâr +%75 | Borsanın Gündemi 26.10 — 26,5 Mr TL
3. Paratic 23.10 — €2,4 Mr sözleşme + BofA 1,5 Mr TL satış
4. Hisse.net 25.10 — €523M | Finans Hattı 21.10 — $442,5M | Finans Hattı 22.10 — hedef 517,20 TL
5. KAP aktarımları 27.10 — Faaliyet Raporu + Sorumluluk Beyanı (net borç ve döviz pozisyonu buradan doğrulanmalı)

*Bu analiz bilgilendirme amaçlıdır; yatırım tavsiyesi değildir.*
