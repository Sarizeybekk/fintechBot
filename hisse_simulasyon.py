# hisse_simulasyon.py

import yfinance as yf
from datetime import datetime
import dateparser

def hisse_simulasyon(hisse_kodu: str, baslangic_input: str, yatirim_tutari: float):
    try:
        # 1. Hisse kodunu düzenle (Türk hisseleri için .IS ekle)
        if not hisse_kodu.endswith('.IS') and len(hisse_kodu) <= 6:
            hisse_kodu = f"{hisse_kodu}.IS"
        
        # 2. Doğal dil tarihini datetime objesine çevir
        baslangic_tarihi = dateparser.parse(baslangic_input)
        if not baslangic_tarihi:
            return {"hata": f"Başlangıç tarihi anlaşılamadı: {baslangic_input}"}

        baslangic_str = baslangic_tarihi.strftime("%Y-%m-%d")
        bugun = datetime.now().strftime("%Y-%m-%d")

        # 3. Veri çek - farklı formatları dene
        df = None
        symbol_variants = [hisse_kodu, hisse_kodu.replace('.IS', ''), f"{hisse_kodu.replace('.IS', '')}.IS"]
        
        for variant in symbol_variants:
            try:
                df = yf.download(variant, start=baslangic_str, end=bugun, progress=False)
                if not df.empty and len(df) >= 2:
                    break
            except:
                continue

        if df.empty or len(df) < 2:
            return {"hata": f"{hisse_kodu} için yeterli veri bulunamadı."}

        # 3. İlk ve son fiyatı al
        ilk_gun_fiyati = df['Close'].iloc[0].item()
        son_fiyat = df['Close'].iloc[-1].item()

        # 4. Hesaplamalar
        lot_sayisi = yatirim_tutari / ilk_gun_fiyati
        simdiki_deger = lot_sayisi * son_fiyat
        kazanc = simdiki_deger - yatirim_tutari
        yuzde_getiri = (kazanc / yatirim_tutari) * 100

        return {
            "hisse": hisse_kodu,
            "başlangıç tarihi": baslangic_str,
            "başlangıç fiyatı": round(ilk_gun_fiyati, 2),
            "güncel fiyat": round(son_fiyat, 2),
            "alınan lot": round(lot_sayisi, 2),
            "şu anki değer": round(simdiki_deger, 2),
            "net kazanç": round(kazanc, 2),
            "getiri %": round(yuzde_getiri, 2)
        }

    except Exception as e:
        return {"hata": str(e)}


if __name__ == "__main__":
    print("Hisse Senedi Simülasyon Aracı")
    print("-------------------------------------")

    hisse = input("Hisse kodunu girin (örn: THYAO.IS, ALARK.IS): ").strip().upper()
    tarih = input("Başlangıç tarihini girin (örn: 1 ay önce, 2023 başı, 2022-01-05): ").strip()
    tutar_input = input("Yatırım tutarı (TL): ").strip()

    try:
        tutar = float(tutar_input)
    except ValueError:
        print(" Geçersiz tutar!")
        exit()

    sonuc = hisse_simulasyon(hisse, tarih, tutar)

    print("\n Simülasyon Sonucu:")
    for k, v in sonuc.items():
        print(f"{k}: {v}")
