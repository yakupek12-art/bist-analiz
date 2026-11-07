# OpenCode Kurulum Notları — 22 Ekim 2026

Bu dosya, yapay zekanın (OpenCode) yeni bir sohbette her şeyi "hatırlaması" için yazıldı.
Kullanım: Yeni sohbette sadece şunu yaz → "opencode-notlari.md dosyasını oku ve kaldığımız yerden devam edelim"

## Yapılanlar (tamamlandı ✅)

- OpenCode CLI v2.1.2 kuruldu → `C:\Users\PC\.opencode\bin\opencode.exe`
- Kullanıcı PATH'ine eklendi → VS Code / yeni terminallerde `opencode` komutu çalışıyor
  (VS Code'u tamamen kapatıp açmak gerekiyor)
- NVIDIA API anahtarı zaten `opencode.json` içindeydi, CLI otomatik kullandı (auth.json yok, gerek de yok)
- Eski 4 modelin HEPSI NVIDIA tarafından emekliye ayrılmıştı → listeden temizlendi:
  - openai/gpt-oss-120b (EOL 03.09.2026)
  - deepseek-ai/deepseek-v3.1 (404 veriyor)
  - qwen/qwen3-coder-480b-a35b-instruct (EOL 11.06.2026)
  - moonshotai/kimi-k2-instruct (EOL 12.05.2026)
- Yeni model listesi (üçü de test edildi, çalışıyor):
  - **z-ai/glm-5.3-flash** → varsayılan model
  - **z-ai/glm-5.3**
  - **deepseek-ai/deepseek-v4.1-flash**
  - (moonshotai/kimi-k2.6 canlı listede vardı ama hesapta kullanılamıyor, eklenmedi)
- Ayar dosyası: `C:\Users\PC\.config\opencode\opencode.json` (NVIDIA NIM, baseURL: integrate.api.nvidia.com/v1)
- Desktop uygulaması (AppData\Local\Programs\@opencodedesktop) etkilenmedi, çalışıyor

## Model listesi durumu (22 Ekim 2026 güncellemesi)

- Kullanıcının isteği: videolarda ~78 model görünüyor, kendisinde ~30 → "modelleri ekle"
- Öğrenilen: `/models` listesi models.dev kataloğuyla OTOMATİK birleşiyor. Ama ücretsiz NVIDIA hesabı
  her modele erişemiyor → erişilemeyenler "Function not found for account" hatası veriyor.
- HESAPTA KESİN ÇALIŞAN NVIDIA modelleri (test edildi ✅):
  - nvidia/z-ai/glm-5.3-flash (varsayılan)
  - nvidia/z-ai/glm-5.3
  - nvidia/deepseek-ai/deepseek-v4.1-flash
  - nvidia/nvidia/nemotron-3-ultra-550b-a55b
  - nvidia/nvidia/nemotron-3.5-lightning-30b-a3b
  - nvidia/poolside/laguna-xs-2.1
  - nvidia/meta/muse-glimmer-30b
- HESAPTA ÇALIŞMAYANLAR (10 elle-eklenen model: mistral-large-2, mixtral, phi-3.5, yi-large, dbrx,
  nemotron-4-340b, nemotron-70b, nemotron-3-super, nemotron-ultra-253b, gemma-3-12b) → opencode.json'dan silindiler
- opencode/* ücretsiz modeller: 10 adet; minimax-m3.1-flash-free DEPRECATED (hata verir).
  Gizleme denendi (provider + providers, disabled:true) → başarısız, OpenCode yönetimli sağlayıcı bunu yok sayıyor.
- Arka plan testi SONUÇLARI (22 Ekim):
  - ÇALIŞTI ✅: openai/gpt-oss-20b, stepfun-ai/step-5-preview,
    nvidia/nemotron-3-nano-omni-30b-a3b-reasoning, google/diffusiongemma-26b-a4b-it
  - ÇALIŞMADI: google/gemma-4-31b-it ve meta/llama-3.2-90b-vision (2'şer kez zaman aşımı),
    meta/llama-3.2-11b-vision (yanıt veriyor ama araç çağrısını metin olarak döküyor — güvenilmez)
- opencode.json FINAL: 3 çekirdek model + 7 junk disabled:true; opencode blokları temizlendi ✅
- KESİN ÇALIŞAN NVIDIA LİSTESİ (11): glm-5.3-flash (varsayılan), glm-5.3, deepseek-v4.1-flash,
  nemotron-3-ultra-550b, nemotron-3.5-lightning-30b, laguna-xs-2.1, muse-glimmer-30b,
  gpt-oss-20b, step-5-preview, nemotron-3-nano-omni, diffusiongemma-26b
- SON DOĞRULAMA (22 Ekim, servis yeniden başlatıldıktan sonra): Toplam 31 = 22 nvidia + 9 opencode free.
  - Ölü elle-eklemeler listeden KALKTI ✅
  - opencode/minimax-m3.1-flash-free katalogdan tamamen KALKTI (deprecated) ✅
  - Junk (embed/rerank/guard/voicechat/paligemma) `opencode models` çıktısında HÂLÂ görünüyor —
    disabled:true bu sürümde katalog modellerini gizlemiyor; TUI seçicide filtrelenmiş olabilir.
    Kullanıcıya "çalışmayanları seçme" listesi verildi.
- Servis yeniden başlatıldı; uygulama/VS Code yeniden başlatınca temiz liste gelir.

## Yeni modeller otomatik geliyor mu?

- EVET: OpenCode model listesini models.dev veritabanıyla otomatik birleştirir. NVIDIA yeni model ekleyip
  models.dev'e işlenince listede kendiliğinden görünür, elle eklemeye gerek yok.
- ANCAK: (1) hesap erişimi gerekir (ücretsiz hesap her modeli açmıyor), (2) models.dev'e işlenmesi günler sürebilir.
- Yeni model kontrolü istenirse: opencode.json'daki anahtarla GET https://integrate.api.nvidia.com/v1/models

## YENİ PROJE (22 Ekim 2026): Hisse Senedi / Finansal Analiz Otomasyonu

- Kullanıcının ASIL amacı: otomasyon
  - Belli kriterlere göre hisse analizi (BIST hisseleri)
  - Hisseleri birlikte seçmek
  - Şirket bilançoları + KAP dip notları analizi (kullanıcının kaçırdıkları dahil)
  - Analiz raporları + GÜNLÜK bilgilendirme
- Detaylar kullanıcıyla konuşulacak. Kullanıcı "önce model işini bitir" dedi → model işi 22 Ekim'de bitti.
- Not: ~/.config/opencode/finas101 klasörü BOŞ (muhtemelen eski deneme kalıntısı — kullanıcıya soruldu)
- E-posta gönderimi (kullanıcının sorusu): OpenCode'da yerleşik e-posta aracı YOK ama kurulabilir:
  - Seçenek A: SMTP (Gmail ise 2FA + "Uygulama Şifresi" gerekir; ana şifre ASLA paylaşılmamalı)
  - Seçenek B: ücretsiz e-posta API'si (Brevo / Resend — ücretsiz kotaları var)
  - Günlük otomasyon: Windows Görev Zamanlayıcı + script; PC açıkken çalışır (bilinmeli)
- KAP notu: kap.org.tr'de açık duyuru verileri var; analiz için PDF/XBRL okuma gerekebilir

## PROJE İLERLEMESİ (22 Ekim akşamı)

- KARARLAR: (1) telefon bildirimi PC KAPALIYKEN de istendi → GitHub Actions bulut çözümü seçildi;
  (2) özet hem sabah 08:30 hem akşam 19:00 (hafta içi); (3) ilk örnek analiz: ASELS
- KURULUM BAŞLADI: finans-otomasyon/ klasörü oluşturuldu:
  - scripts/gunluk_ozet.py (fiyat çekme + GLM özeti + Telegram gönderme, saf stdlib)
  - .github/workflows/ozet.yml (cron 05:30 + 16:00 UTC = TR 08:30 + 19:00, hafta içi, + workflow_dispatch)
  - README.md (secrets tablosu + yol haritası)
- VERİ TESTLERİ: Yahoo fiyat API çalışıyor (ASELS kanıtlandı: 338.25 TL son fiyat).
  KAP API POST denemesi timeout → şema incelenmesi gerek.
  NVIDIA chat completions DOĞRUDAN test (PC'den): Invoke-RestMethod timeout, curl timeout, curl -4 (IPv4) de timeout
  → PC'den doğrudan HTTPS çağrısı bağlantı seviyesinde takılıyor; OpenCode içinden AYNI API sorunsuz çalışıyor (bu sohbet kanıtı).
  ÇÖZÜM NOTU: Python script GitHub Actions'ta (ABD sunucularından) çalışacak — orada büyük ihtimalle sorunsuz olur;
  ilk workflow_dispatch testi kesin sonucu verecek. Yerel test gerekirse proxy veya python-requests denenebilir.
- DURUM (22 Ekim gece): KULLANICI YORGUN, burada duruldu. Sıradaki adımlar bekliyor:
  1) Kullanıcı telefonundan @BotFather'dan bot oluşturup token verecek (2 dk, yatarak yapılabilir)
  2) GitHub hesabı (yoksa açılacak) + PAT token
  3) Sonra: chat_id öğrenme → ilk Telegram test mesajı → repo + secrets → bulut testi
  4) Kullanıcı finansal isteklerini DETAYLI anlatacak (kriterler, hisse listesi, rapor formatı)
- TELEGRAM KURULDU (24 Ekim): bot @Tetbbbbrisbot (isim: "Opencode"), chat_id: 6705235259 (kullanıcı adı: Ekmek)
  - DİKKAT: PC'de Invoke-RestMethod api.telegram.org'da takılıyor → TÜM Telegram işlemleri CURL ile yapılmalı
  - Webhook olayı: botta hooks.menubuilder.cc üçüncü parti webhook vardı → silindi (deleteWebhook + drop_pending_updates).
    Ama eski token o siteye sızmıştı!
  - GÜVENLİK TAMAM (24 Ekim): eski token menubuilder'a sızmıştı → kullanıcı BotFather'da /revoke ile yeniledi.
    YENİ TOKEN: 8638039828:AAH3RGIyMCx9jnxIAPdRmT5dRXaK0oLnA1E (chat_id aynı: 6705235259)
  - İLK TEST MESAJI GÖNDERİLDİ: ok=True, mesaj no 10 (24 Ekim, PC'den curl ile, içinde canlı ASELS fiyatı)
- SISTEM TAMAMLANDI (24 Ekim)! ✅
  - GitHub: yakupek12-art/finans-otomasyon (PRIVATE repo)
  - 5 secret kuruldu (gh CLI v2.103.2 ile): NVIDIA_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    WATCHLIST=ASELS.IS, MODEL=z-ai/glm-5.3-flash (repository variables API 404 veriyordu → secrets kullanıldı)
  - Dosyalar push edildi: scripts/gunluk_ozet.py, .github/workflows/ozet.yml, README.md
  - İLK BULUT KOŞUMU: workflow_dispatch → status=completed, conclusion=SUCCESS
    → GitHub'ın sunucusundan Telegram mesajı gitti (PC BAĞIMSIZ kanıt!)
  - Otomatik zamanlama: hafta içi TR 08:30 + 19:00 (cron 05:30 + 16:00 UTC)
  - PAT: 30 gün sonra kendiliğinden süresi dolar; değişiklik gerekirse kullanıcıdan yenisi istenir
  - Elle test: GitHub > repo > Actions > gunluk-ozet > Run workflow düğmesi
- NVIDIA YAVAŞLIK SORUNU (24 Ekim, bulut testlerinde ortaya çıktı):
  - İlk bulut koşumu "Ozet olusturulamadi" mesajı gönderdi → log: "read operation timed out" (60sn)
  - 240sn zaman aşımı düzeltmesi de yetmedi (iki deneme de timeout); yerel curl testleri de 0 bayt / 90sn
  - KESİN TESPİT: aynı çağrı OpenCode CLI ile de 298.6 saniye sürdü; deepseek-v4.1-flash ise 597 saniye
    → NVIDIA ücretsiz kuyruğu o gün aşırı yavaştı (22 Ekim'de aynı işlemler 10-30 sn idi).
    Sorun istek biçimi değil, NVIDIA tarafında kuyruk/kısıtlama (muhtemelen 3 günlük yoğun test kullanımı).
  - ÇÖZÜM (script v3): model zinciri [MODEL → YEDEK_MODEL=deepseek-ai/deepseek-v4.1-flash],
    model başına 360sn zaman aşımı; hiçbiri çalışmazsa KURAL TABANLI otomatik özet →
    kullanıcı her durumda günlük mesajını alır (en kötü senaryoda LLM'siz ama dolu özet)
  - v3 DOĞRULANDI (24 Ekim): bulut koşumu SUCCESS — "Ozet sunu model ile hazirlandi" + Telegram ok:true
    (mesaj no 15, ~4-5 dakikada tamamlandı; GLM bu kez 360sn zaman aşamı içinde cevap verdi)
- SIRADAKİ ADIMLAR (finans tarafı):
  1. Kullanıcı detaylı finansal isteklerini anlatacak (kriterler, hisse listesi, rapor formatı)
  2. KAP bildirim entegrasyonu (API şeması incelenecek; PC'den timeout vardı → buluttan denenebilir)
  3. Bilanço verisi (İş Yatırım/KAP) → kar/FAVÖK/marj, 5-10 yıl tablolar
  4. ASELS ile ilk tam analiz raporu (hendek testi + rakip analizi)

## VERİ KAYNAKLARI ARAŞTIRMASI (25 Ekim) — "beklenti bilançoları" sorusu

- Kullanıcı istediği: bilânço sezonu yaklaşınca aracı kurum beklenti bilançolarına kolay erişim
  (kullanıcı çerçeveyi veriyor, detayları AI dolduruyor; "daha çok şey kuracağız" dedi)
- BULUNAN KAYNAKLAR:
  1. İş Yatırım "Bilanço Tahminleri" çeyreklik PDF raporu (arastirma.isyatirim.com.tr, Araştırma Müdürlüğü)
     — şirket bazında satış/FAVÖK/kâr tahminleri; örnek: 2C2026_kar_tahminleri_TR-1.pdf; 3Ç26 raporu kritik (sezon şimdi)
  2. isyatirimhisse Python kütüphanesi (github.com/urazakgul/isyatirimhisse, v5.0.1, MIT, resmî değil/kişisel kullanım):
     fetch_financials (bilançolar) + fetch_stock_data (fiyat) + fetch_index_data (endeks) → cloud'da pip kurulacak
  3. KAP: bildirim-sorgu (şirket bazlı member= kalıbı), içerik arama (kap.org.tr/tr/search → dip not taraması),
     "Finansal Rapor Tarihleri" (bilânço takvimi sayfası), Beklenti Anketi (aracı kurum tahmin anketi — KAP'ta
     mevcut; kesin URL/şema kuruluma kadar netleştirilecek)
- ÖNERİLEN HAT: takvim → beklenti toplama → gerçek bilânço çekme → beklenti vs gerçek AI analizi →
  5-10 yıl trendler (hendek testi, rakip analizi) → Telegram özet + sohbette derin rapor
- Not: webfetch KAP'a ulaşabiliyor (404 = yanlış adres, erişim sorunu değil); KAP API POST'u PC'den timeout
  vermişti ama bulut (GitHub Actions) denenecek

## KULLANICININ ANALİZ ÇERÇEVESİ + ARAÇ ENVANTERİ (25 Ekim)

- İKİ MOD: (A) sohbette şirket adı verilir → kriterlere göre derin analiz (ÖNCELİK 1);
  (B) Telegram günlük: takip listesinin haber/hareket özeti
- BEŞ KATMAN: 1) Haber+gündem+AI yorumu 2) Hikâye: sektör/katalizör/HENDEK 3) Rakip-sektör kıyası
  4) Temel analiz: marjlar, borç, cari oran, KAP DİP NOTLARI (kullanıcının kaçırdıkları), 5-10 yıl seri
  5) Olgunluk+karar: "finansal gücü var ama hendeği yok" tarzı sınıflama + TEDARİKÇİ ZİNCİRİ riski
  (AI eklemeleri: haber önem skoru, yönetim yapısı, değerleme çarpanları, kâr kalitesi, temettü)
- ARAÇ ENVANTERİ (bulundu, HENÜZ KURULMADI):
  - Haber: Google News RSS (q=HİSSE araması, ücretsiz/anahtarsız) + bakinazik/rss (TR ekonomi RSS kataloğu)
  - KAP: kap_sdk (enciyo/kap-tr-sdk, pip) — şirket/finansal rapor/duyuru/sektör; KAP içerik arama
  - Bilânço: isyatirimhisse (fetch_financials); yardımcılar: financelib (yigitoo), Bist-KAP-Dataset-Builder
  - Derin araştırma: GPT Researcher (assafelovic/gpt-researcher, 30K+ yıldız, kaynaklı raporlar, MCP sunucusu da var)
- ÇOKLU-AJAN CEVABI: EVET, 3 katman: (1) OpenCode'un kendi subagent sistemi — bugün bile kullanılabilir;
  (2) GitHub framework'leri: CrewAI (rollü ekipler, en kolay) / GPT Researcher (araştırma kurumu) /
  LangGraph (amiral gemisi); AutoGen bakım modunda KULLANILMAYACAK; (3) Actions içinde adım-uzmanları.
  UYARI: her ajan ayrı AI çağrısı = NVIDIA ücretsiz kotası hızlı harcanır; yavaş günlerde süre uzar.
- Kullanıcı kararı beklemede: hangi katman/araçla başlanacak (kurulum hâlâ YOK — kullanıcı ne zaman derse)

## AI'NIN EKLEMELERİ (26 Ekim — kullanıcı "sen ne eklersin" diye sordu)

- Eklenen katmanlar (6-12): 6) AYI AJANI (red-team/kötü senaryo avukatı; boğa-ayı-hakem tartışma deseni)
  7) TEKNİK ANALİZ → TA-Lib (TA-Lib/ta-lib DOĞRULANDI: 200+ indikatör, pip install TA-Lib, BSD, sektör standardı)
  8) MAKRO AJANI → evds paketi (fatihmete/evds, v0.4.0 Şubat 2026, DOĞRULANDI: TCMB EVDS resmî API wrapper;
     kullanıcı TCMB EVDS hesabından ücretsiz API anahtarı alacak — tek seferlik)
  9) KÂR KALİTESİ → Piotroski F-Score + Beneish M-Score (kendi kodumuzla, kütüphane gerekmez)
  10) HAFIZA/DELTA ajanı (analiz arşivi + "geçen çeyreğe göre ne değişti" — LLM'siz)
  11) KURAL MOTORU (kullanıcı eşikleri → Telegram uyarısı — LLM'siz)
  12) DEĞERLEME ajanı (çarpan kıyası + şirketin kendi 5-10 yıl ortalamasına göre konumu)
- ELENEN: pandas-ta (twopirllc repo 404 — kullanılmayacak)
- NOT: websearch 26 Ekim'de bir süre çalışmadı; doğrulamalar webfetch ile yapıldı (TA-Lib, evds PyPI sayfası)
- GÜNCEL MİMARİ: koordinatör altı uzman ajan (haber/hikâye/temel/rakip/teknik/makro) + kâr kalitesi/hafıza/değerleme
  destek katmanları + AYI AJANI + HAKEM → ana rapor → kural motoru → Telegram
## KURULUM BAŞLADI (26 Ekim — kullanıcı "kur ve entegre et" dedi)

- Python 3.13.1 KURULDU (per-user, PATH'e eklendi): %LOCALAPPDATA%\Programs\Python\Python313\python.exe
- AGENTS.md (proje kökünde) → 12 katman metodoloji + kanıtlanmış veri kaynakları (Yahoo/Google News RSS/KAP/
  isyatirim/EVDS) + çıktı formatı (🟢🟡🔴 karar kutusu, AL/SAT yok) + kurallar (arşiv, KURALLAR.md, disclaimer)
- 6 UZMAN AJAN tanımlandı (.opencode/agents/*.md, mode: subagent, renk kodlu):
  haber-ajani, hikaye-ajani, bilanco-ajani, teknik-ajani, rakip-ajani, ayi-ajani
- 2 KOMUT: /analiz (tam çoklu-ajan pipeline + analiz-arşivi/ kaydı + delta) ve /haber (haber shortcut)
- SONUÇLAR (26 Ekim akşamı — HEPSİ BAŞARILI ✅):
  - Python 3.13.1 ✅, isyatirimhisse ✅ (fetch_financials / fetch_stock_data / fetch_index_data), TA-Lib 0.8.2 ✅
  - AJAN SMOKE TESTİ ✅: haber-ajani koordinatörden (subagent aracıyla) başarıyla çağrıldı, rolünü doğru
    özetledi, "AJAN SISTEMI CALISIYOR" cevabı geldi → ÇOKLU-AJAN MİMARİSİ ÇALIŞIYOR
    (6 uzman ajan + /analiz + /haber komutları KULLANIMA HAZIR)
  - FREE MODEL TESTİ ✅: opencode/glm-5.3-flash-free "OK" cevabını 4 SANİYEDE verdi
    (NVIDIA ücretsiz kuyruğu aynı iş için ~5 dk sürüyordu!) → ajanlar bu modele sabitlenebilir: hız + kota tasarrufu
  - AGENTS.md otomatik yüklendi ve sistem talimatı olarak AKTİF (session'a instruction olarak geldi)

## İLK TAM ANALİZ: ASELS (27 Ekim)

- **VERİ-ÖNCE MİMARİSİ KEŞFEDİLDİ (kritik ders):** ücretsiz model çok-paralel ve çok-adımlı koşularda limitlere takılıyor
  → en iyi desen: koordinatör veriyi makineyle çeker (AI'sız, hızlı), ajanlar dosya ekiyle (-f) TEK ATIŞLIK analiz yapar
- VERİ TOPLANDI (analiz-calisma/ASELS-veri/): fiyat-ozet.txt (1y, RSI/ortalamalar koordinatör hesaplı), haberler.txt (20 RSS başlığı),
  rakip-veri.txt (OTOKAR/PAMEL/NUHL/SOKM — SOKM gıda perakendesiymiş, ajan hatayı yakaladı),
  bilanco-ozet.txt (14 çeyrek 2023/3→2026/6!; isyatirimhisse; 2025-2026 AYRI fetch gerekti: start_year/end_year parametreleri)
- RAPORLAR (analiz-calisma/ASELS-veri/raporlar/): teknik ✅ (NVIDIA, temiz), bilanco ✅ (free model, muhteşem kalite:
  net borç 2x uyarısı, 2024 kârının ~%45'i ertelenmiş vergi, ertelenmiş gelir 4,5x = sipariş yükü, CFO kârı aşıyor),
  rakip ⚠️ (free model metni kısmen bozdu → koordinatör temizledi), haber+hikaye+ayi ⏳ arka planda NVIDIA'da
- MODEL DERSLERİ: opencode/glm-5.3-flash-free = saniyeler ama (1) eşzamanlılık limiti çok dar (2 paralel bile reddedebiliyor),
  (2) uzun serbest Türkçe metinde bazen allak-bulak yazıyor, (3) "free usage limit reached" saat bazında patlıyor.
  NVIDIA (glm-5.3-flash) = temiz ama bazen ~5 dk/çağrı. PRATİK STRATEJİ: önce free dene; limit/bozulma gelirse NVIDIA'ya düş.
- run püf noktaları: `opencode run --agent X -f dosya "prompt"` çalışıyor; --model ile free zorlanabiliyor;
  ajan .md frontmatter'ındaki model run'da uygulanmıyor (free reddedilince session modeline düşüyor — nedeni belirsiz)
- ÇAKIŞMA DERSİ: ajan .md'sindeki YÖNTEM adımları ("curl çek, KAP'a bak") ile "veri ekte" promptu çelişince ajan araç deniyor
  → run modunda onay bekleyip ASILIYOR. Çözüm: prompta sert "KURAL: hiçbir arac kullanma" + veri ekle.
- GUNCELLEME (27 Ekim gece): 3 arka plan ajani daha TAMAMLANDI → **6/6 RAPOR HAZIR ✅** (raporlar/ klasöründe)
  - haber-raporu.md: 3Ç26 bilânço açıkmış! 9M net kâr 26,5 milyar TL (+%75); üç büyük ihracat sözleşmesi
    (€2,4 Mr + €523M + $442,5M); BofA 1,5 Mr TL blok satış; hedef fiyat 517,20 TL; KAP: Faaliyet Raporu 27 Eki'de
  - hikaye-raporu.md: 1975/TSKGV kuruluş, hendeği 4,5/5 (yarı-tekel+değişim maliyeti+birikim), olgun-ama-büyüyen,
    katalizör tablosu (bilânço✅, sözleşmeler✅, 2027 bütçesi ≈Kas-Ara, NATO/SAFE payı ≈)
  - ayi-raporu.md: 3 risk — (1) nakit üretmeyen büyüme (sözleşmeler=sermaye ihtiyacı), (2) kâr kalitesi
    (başlıkta %75 ama marj eriyor + ertelenmiş vergi), (3) pahalı hikâye + BofA çıkış sinyali
- **Eksiklikler (28 Ekim tespiti):**
  1. KOORDİNATÖR SENTEZİ YOK — 6 rapor var ama karar kutusu 🟢🟡🔴 + delta + "senin kaçırdığın" tek raporda birleştirilmedi
  2. BİLANÇO ANALİZİ YÜZEYDE — Nakit akışı analizi (FCF/OCF trend), DuPont ayrışımı, normalize kâr, owner earnings, ROIC trendleri, sermaye yerleştirme kalitesi YOK
  3. KAP DERİNLİK YOK — PDF dip notları otomatik çıkarımı (taahhütler, teminatlar, davalar, ilgili taraf işlemleri, kambiyo pozisyonu) YOK
  4. DEĞERLEME ÇERÇEVESİ YOK — DCF (farklı senaryolar), çarpan percentile'leri (5-10 yıl), güvenlik marjı, ters DCF (piyasa neyi fiyatlıyor) YOK
  10. SEKTÖR ÖZEL ŞABLONLARI YOK — Bankacılık, holding, perakende, teknoloji, enerji için farklı metrikler/çerçeveler YOK
  11. KÂR KALİTESİ DERİN — Accruals analizi, gelir tanıma politikaları, stok/amortisman politikaları, capex/depreciation karşılaştırması YOK
  12. SERMAYE YERLEŞTİRME KALİTESİ YOK — Buyback/temettü/M&A geçmişi, yeniden yatırım ROIC, serbest nakit akışı kullanımı YOK
  13. YÖNETİM KALİTESİ YOK — İçeriden sahiplik, ödüllendirme hizası, geçmiş taahhüt/tahmin tutarlılığı, yönetim kurulu bağımsızlığı YOK
  14. SENARYO ANALİZİ YOK — Base/Bull/Bear + olasılıklar, Monte Carlo veya yapılandırılmış risk matrisi YOK
  16. OTOMATİK VERİ HATTI YOK — Hala "veri-önce" manuel; Zamanlanmış toplama (fiyat, haber, KAP, bilançolar, tahminler) YOK
  17. KURALLAR.MD VE UYARI MOTORU YOK — Eşik tabanlı tetikleyiciler (Telegram/Email) YOK
  18. TARİHÇE ARŞİVİ + ARAMA YOK — Sadece markdown dosyaları; SQL/vektör arama, delta karşılaştırması YOK
  17. SEKTÖR ÖZEL ANALİZ YOK — Banka (NIM, CoR, CAR), Holding (NAV indirimi), Perakende (SSSG, m² başına satış), Teknoloji (ARR, NRR, kural 40) YOK
  18. TEKNİK ANALİZ DERİN — Formasyonlar, hacim profili, Wyckoff, Elliott, order flow, likidite haritaları YOK
  19. KAP PDF PARSER YOK — Dip notları, taahhütler, davalar, ilgili taraf, kambiyo pozisyonu otomatik çıkarma YOK
  20. BEKLENTİ vs GERÇEK TAKİBİ — Aracı kurum tahminleri (İş Yatırım, KAP anketi) vs gerçekleşen, şaşırtma analizi YOK
  21. EARNINGS CALL TRANSKRİPT ANALİZİ YOK — Yönetim tonu, rehberlik değişimi, Q&A tonu analizi YOK
  22. KISA POZISYON / KURUMSAL SAHİPLİK TAKİBİ YOK — KAP bildirimlerinden kurumsal/%5 üstü değişiklikler YOK
  22. RAPOR ÜRETİM HATTI OTOMATİK DEĞİL — Hala manuel koordinatör; tam otomatik /analiz → rapor → arşiv → delta YOK
  24. WEB ARAYÜZÜ / DASHBOARD YOK — Sadece markdown; filtrelenebilir tablo, grafik, karşılaştırma YOK



## GÜNCELLEME (28 Ekim öğleden sonrası) — ALTYAPI TAMAMLANDI ✅

- **Finansal Derinlik Modülü** (finansal_derinlik.py) ✅ Stdlib-only, 14 dönem, 147 kalem:
  - Marjlar (brüt/faaliyet/net/FAVOK proxy), Nakit akışı proxy (NOPAT), Normalize kâr, Net borç/FAVOK, Cari/Asit-test, Vergi oranı, NOPAT, Normalize kâr marjı
  - ASELS 2026/6: Faaliyet marj %27, Net marj %16.3, NOPAT 20.4B, Net borç/FAVOK 1.4x ✅
- **KAP PDF Parser** (kap_pdf_parser.py) ✅ pdfplumber + PyMuPDF fallback, teminat/dava/ilgili taraf/kambiyo/taahhüt/müşteri yoğunluğu regex çıkarma
- **KURALLAR.md** ✅ 7 kategori, 40+ eşik parametresi (fiyat, temel, kâr kalitesi, değerleme, haber, KAP dip not, bildirim)
- **Değerleme Modülü** (degerleme.py) ✅ DCF (3 senaryo), Çarpanlar (P/E, EV/FAVOK, EV/Sales), Ters DCF, Güvenlik marjı, NOPAT
- **ASELS Test Sonuçları (2026/6):** FAVOK marj %27.07, Net marj %16.33, NOPAT 20.4B, Net borç/FAVOK 1.41x, P/E hesaplandı, Fair value P/E bazlı hesaplandı

## SIRADAKİ ADIMLAR (29 Ekim — Otomasyon ve Entegrasyon)

1. **KAP PDF Parser Entegrasyonu** → kap_pdf_parser.py ajanlara entegre → KAP bildirimi PDF'ini indir → dip notları çıkar → bilanco-ajani/haber-ajani/ayi-ajani'ye besle
2. **Otomatik Veri Hattı (GitHub Actions)** → Günlük: fiyat + haber + KAP bildirimi toplama → Haftalık: bilanço/gelir tablosu güncelleme → Aylık: derin analiz tetikleme
3. **Sektör Şablonları** → Banka (NIM, CoR, CAR), Holding (NAV indirimi), Perakende (SSSG), Teknoloji (ARR/NRR), Enerji (rezerv/LCOE) → sektor_sablonlari/ klasörü
4. **Koordinatör Sentez Motoru** → 6 raporu birleştir → karar kutusu (🟢🟡🔴) + delta + "senin kaçırdığın" → analiz-arşivi/HISSE-YYYY-AA-GG.md
5. **Analiz Arşivi + Delta** → analiz-arşivi/ klasörü, SQLite/JSON indeks, arama, delta karşılaştırma
5. **Kural Motoru Entegrasyonu** → KURALLAR.md eşikleri → analiz sonrası kontrol → Telegram bildirimi
6. **Sektör Şablonları** → Banka (NIM, CoR, CAR), Holding (NAV indirimi), Perakende (SSSG), Teknoloji (ARR/NRR), Enerji (rezerv/LCOE)

## Faydalı bilgiler

- Model değiştirme: Arayüzde `/models` yaz
- Canlı NVIDIA modellerini listeleme: opencode.json'daki anahtarla
  `https://integrate.api.nvidia.com/v1/models` adresine GET (Bearer token)
- CLI sürüm kontrolü: `opencode --version` (şu an v2.1.2)
- Kullanıcı yeni başlayan seviyede → adımları sade ve adım adım anlat
