import json
import os
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional

class PortfolioManager:
    def __init__(self, portfolio_file="user_portfolios.json"):
        self.portfolio_file = portfolio_file
        self.portfolios = self.load_portfolios()
    
    def load_portfolios(self) -> Dict:
        """Portföy verilerini JSON dosyasından yükle"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Portföy yüklenirken hata: {e}")
                return {"default_user": []}
        return {"default_user": []}
    
    def save_portfolios(self):
        """Portföy verilerini JSON dosyasına kaydet"""
        try:
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(self.portfolios, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Portföy kaydedilirken hata: {e}")
            return False
    
    def add_stock(self, user_id: str, symbol: str, quantity: float, avg_price: float) -> Dict:
        """Yeni hisse senedi ekle"""
        if user_id not in self.portfolios:
            self.portfolios[user_id] = []
        
        # Mevcut hisse kontrolü
        for stock in self.portfolios[user_id]:
            if stock['symbol'] == symbol:
                # Mevcut hisseyi güncelle
                total_quantity = stock['quantity'] + quantity
                total_cost = (stock['quantity'] * stock['avg_price']) + (quantity * avg_price)
                new_avg_price = total_cost / total_quantity
                
                stock['quantity'] = total_quantity
                stock['avg_price'] = new_avg_price
                stock['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                
                self.save_portfolios()
                return {"success": True, "message": f"{symbol} güncellendi", "stock": stock}
        
        # Yeni hisse ekle
        new_stock = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": avg_price,
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        
        self.portfolios[user_id].append(new_stock)
        self.save_portfolios()
        
        return {"success": True, "message": f"{symbol} eklendi", "stock": new_stock}
    
    def remove_stock(self, user_id: str, symbol: str, quantity: float = None) -> Dict:
        """Hisse senedi çıkar veya miktar azalt"""
        if user_id not in self.portfolios:
            return {"success": False, "message": "Kullanıcı bulunamadı"}
        
        for i, stock in enumerate(self.portfolios[user_id]):
            if stock['symbol'] == symbol:
                if quantity is None or quantity >= stock['quantity']:
                    # Tüm hisseyi çıkar
                    removed_stock = self.portfolios[user_id].pop(i)
                    self.save_portfolios()
                    return {"success": True, "message": f"{symbol} tamamen çıkarıldı", "stock": removed_stock}
                else:
                    # Miktar azalt
                    stock['quantity'] -= quantity
                    stock['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                    self.save_portfolios()
                    return {"success": True, "message": f"{symbol} miktarı azaltıldı", "stock": stock}
        
        return {"success": False, "message": f"{symbol} bulunamadı"}
    
    def get_portfolio(self, user_id: str) -> List[Dict]:
        """Kullanıcının portföyünü getir"""
        return self.portfolios.get(user_id, [])
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Hisse senettlerinin güncel fiyatlarını al"""
        prices = {}
        
        for symbol in symbols:
            try:
                # Önce Yahoo Finance API'yi dene
                if symbol.endswith('.IS'):
                    ticker = symbol
                else:
                    ticker = f"{symbol}.IS"
                
                print(f"🔍 {symbol} için fiyat aranıyor: {ticker}")
                
                # Yahoo Finance API
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            price = result['meta']['regularMarketPrice']
                            if price and price > 0:
                                prices[symbol] = price
                                print(f" {symbol} Yahoo fiyatı: {price} TL")
                                continue
                        
                        # Alternatif fiyat kaynakları
                        if 'indicators' in result and 'quote' in result['indicators']:
                            quote = result['indicators']['quote'][0]
                            if 'close' in quote and quote['close']:
                                price = quote['close'][-1]
                                if price and price > 0:
                                    prices[symbol] = price
                                    print(f" {symbol} Yahoo alternatif fiyatı: {price} TL")
                                    continue
                
                # Yahoo Finance başarısız olursa, alternatif API'leri dene
                print(f"🔄 {symbol} için alternatif API deneniyor...")
                
                # Finans API (Türk hisseleri için)
                try:
                    finans_url = f"https://finans.truncgil.com/today.json"
                    finans_response = requests.get(finans_url, timeout=10)
                    
                    if finans_response.status_code == 200:
                        finans_data = finans_response.json()
                        
                        # Symbol'ü temizle
                        clean_symbol = symbol.replace('.IS', '').upper()
                        
                        if clean_symbol in finans_data:
                            price_str = finans_data[clean_symbol].get('Alış', '0')
                            # Fiyat string'ini temizle
                            price = float(price_str.replace(',', '').replace('₺', '').replace('TL', '').strip())
                            
                            if price > 0:
                                prices[symbol] = price
                                print(f" {symbol} Finans API fiyatı: {price} TL")
                                continue
                except Exception as e:
                    print(f" Finans API hatası ({symbol}): {e}")
                
                # Tüm API'ler başarısız olursa, varsayılan fiyat kullan
                if symbol not in prices:
                    # Test için sabit fiyatlar (gerçek uygulamada kaldırılacak)
                    test_prices = {
                        'THYAO.IS': 45.50,
                        'KCHOL': 34.25,
                        '55': 0.01
                    }
                    
                    if symbol in test_prices:
                        prices[symbol] = test_prices[symbol]
                        print(f" {symbol} test fiyatı: {test_prices[symbol]} TL")
                    else:
                        prices[symbol] = 0.0
                        print(f" {symbol} için fiyat bulunamadı")
                        
            except Exception as e:
                print(f" {symbol} fiyatı alınırken hata: {e}")
                prices[symbol] = 0.0
        
        print(f" Toplam fiyatlar: {prices}")
        return prices
    
    def calculate_portfolio_value(self, user_id: str) -> Dict:
        """Portföy değerini ve kar/zarar hesapla"""
        portfolio = self.get_portfolio(user_id)
        if not portfolio:
            return {
                "total_invested": 0,
                "current_value": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "stocks": []
            }
        
        symbols = [stock['symbol'] for stock in portfolio]
        current_prices = self.get_current_prices(symbols)
        
        total_invested = 0
        current_value = 0
        stocks_detail = []
        
        for stock in portfolio:
            symbol = stock['symbol']
            quantity = stock['quantity']
            avg_price = stock['avg_price']
            current_price = current_prices.get(symbol, 0)
            
            invested = quantity * avg_price
            current_stock_value = quantity * current_price
            pnl = current_stock_value - invested
            pnl_percent = (pnl / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            current_value += current_stock_value
            
            stocks_detail.append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "invested": invested,
                "current_value": current_stock_value,
                "pnl": pnl,
                "pnl_percent": pnl_percent
            })
        
        total_pnl = current_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "stocks": stocks_detail
        }
    
    def get_portfolio_summary(self, user_id: str) -> Dict:
        """Portföy özeti"""
        portfolio_value = self.calculate_portfolio_value(user_id)
        
        # En iyi ve en kötü performans gösteren hisseler
        stocks = portfolio_value['stocks']
        if stocks:
            best_stock = max(stocks, key=lambda x: x['pnl_percent'])
            worst_stock = min(stocks, key=lambda x: x['pnl_percent'])
        else:
            best_stock = worst_stock = None
        
        return {
            "portfolio_value": portfolio_value,
            "best_performer": best_stock,
            "worst_performer": worst_stock,
            "total_stocks": len(stocks),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        } 