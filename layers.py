# -*- coding: utf-8 -*-
"""
Katman tanimlari - OpenCode agent'siz, NVIDIA API direct
Tum karakterler ASCII guvenli
"""

import os
import json

# Template dosyalarini oku
def load_template(name):
    path = os.path.join(os.path.dirname(__file__), 'templates', name + '.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

layers = [
    {
        "name": "sektor-ajani",
        "desc": "Katman 1: Sektor Makro",
        "files": "veri/sektor_veri.json veri/sektor_peerler.txt veri/makro_veri.json",
        "system": "Sen BIST sektor analistisin. Verilen sektor verilerini, peer medyanlarini, makro verileri analiz et. Cikti: Markdown rapor (Tablo + Anlatim). Sadece rapor yaz, aciklama yapma.",
        "user_template": "sektor-ajani"
    },
    {
        "name": "hikaye-ajani",
        "desc": "Katman 2: Hikaye & Strateji",
        "files": "veri/hikaye_veri.json veri/bilanco.csv veri/kap_yatirim_planlari.txt",
        "system": "Sen BIST sirket hikayesi analistisin. Sirketin kimligini, asil para kaynagini, gelecek yatirimlarini, kapasite genisletme planlarini analiz et. Cikti: Markdown rapor (Tablo + Anlatim).",
        "user_template": "hikaye-ajani"
    },
    {
        "name": "hendek-ajani",
        "desc": "Katman 3: Hendek (Moat) - 5/10 Yil",
        "files": "veri/hendek_veri.json veri/rakip_giris_bariyerleri.txt veri/kriz_performans.txt",
        "system": "Sen hendek (moat) analistisin. 5-10 yil veriyle fiyatlama gucu, kriz dayanikligiligi, ag etkisi, gecis maliyeti, rakip giris bariyerlerini analiz et. Cikti: Markdown rapor (Tablo + Skorlama 0-100).",
        "user_template": "hendek-ajani"
    },
    {
        "name": "rakip-ajani",
        "desc": "Katman 4: Rakip Derin Analizi",
        "files": "veri/rakip_veri.json veri/rakip_karsilastirma.json veri/sektor_veri.json",
        "system": "Sen rakip analistisin. Secili rakipleri derin analiz et: 5-10 yl karlilik, urun farklastirmasi, maliyet avantaji, pazar payi trendi. Cikti: Markdown rapor (Karsilastirma tablolari + Tehdit matrisi).",
        "user_template": "rakip-ajani"
    },
    {
        "name": "yonetim-ajani",
        "desc": "Katman 5: Yonetim / Hakim Ortak Guvenilirligi",
        "files": "veri/yonetim_veri.json",
        "system": "Sen yonetim kalitesi analistisin. Hakim ortak profili, YK bagimsizligi, soz tutarliligi, hisse alim/satim, cikar catismalari analiz et. Cikti: Markdown rapor (Profil tablolari + Skorlama 0-100).",
        "user_template": "yonetim-ajani"
    },
    {
        "name": "sektor-karsilastirma-ajani",
        "desc": "Katman 6: Sektor Ortalamasi vs Sirket",
        "files": "veri/sektor_karsilastirma.json veri/sektor_veri.json veri/finansal_derinlik.json",
        "system": "Sen sektor karsilastirma analistisin. Sirketi sektor medyan/ortalamasi ve en iyi/kotu peerlerle karsilastir. Marjlar, karlilik, degerleme, pazar payi. Cikti: Markdown rapor (Tablo + Karsilastirma + Karar).",
        "user_template": "sektor-karsilastirma-ajani"
    },
    {
        "name": "risk-ajani",
        "desc": "Katman 7: Duyarlilik ve Risk Analizi",
        "files": "veri/duyarlilik_veri.json veri/makro_veri.json veri/ihale_bagimliligi.txt veri/kredi_kosullari.txt",
        "system": "Sen risk analistisin. Sirketin duyarlilik katsayilarini (FX, petrol, faiz, ihale), hedge etkinligi, makro sok senaryolari, kirilma noktalari, ihale/kredi riskini analiz et. Cikti: Markdown rapor (Duyarlilik tablosu + Sok senaryolari + Kirilma noktalari).",
        "user_template": "risk-ajani"
    },
    {
        "name": "degerleme-ajani",
        "desc": "Katman 8: Degerleme (Hendekli vs Hendeksiz)",
        "files": "veri/degerleme_girdi.json veri/finansal_derinlik.json veri/hendek_skor.json",
        "system": "Sen degerleme analistisin. Hendek durumuna gore dogru yontemi uygula: Hendekliyse DCF/Carpan Percentile/Ters DCF/Guvenlik Marji; Hendeksizse NC>0, CFO>NC, ROA artis, Borc/Ozkaynak dusus, Cari dusus, Sermaye artirimi yok, Marj artisi, Asset turnover artisi. Cikti: Markdown rapor (DCF tablosu + Percentile + Ters DCF + Karar).",
        "user_template": "degerleme-ajani"
    },
    {
        "name": "bilanco-ajani",
        "desc": "Katman 9: Bilanco Derin Okuma (5-10 Yil)",
        "files": "veri/bilanco.csv veri/finansal_derinlik.json veri/kap_dip_notlari.txt",
        "system": "Sen bilanco analistisin. 5-10 yillik bilanco/gelir/nakit akim tablosunu derinlemesine oku. Yillik tablolar + anlatim: Ciro->Net Kar, Marjlar, Borc, Nakit Akisi, Oranlar, KAP dip notlari. 'Ne anliyorum?' anlatimi. Cikti: Markdown rapor (6 Tablo + Anlatim + Karar).",
        "user_template": "bilanco-ajani"
    },
    {
        "name": "teknik-ajani",
        "desc": "Katman 10: Teknik Analiz ve Pozisyon Belirleme",
        "files": "veri/teknik.json veri/fiyat.json veri/hacim_profili.json",
        "system": "Sen teknik analistisin. Uzun vadeli value investing icin giris/cikis seviyeleri, pozisyon buyuklugu, stop-loss, R/R, Fibonacci, hacim profili. Cikti: Markdown rapor (Trend + Destek/Direnç + Giris/Cikis bolgeleri + Stop/R/R + Kelly).",
        "user_template": "teknik-ajani"
    }
]