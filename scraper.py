import requests
from bs4 import BeautifulSoup
import csv
import datetime
import os
import re
import json
from urllib.parse import urljoin

class MiyagiRiverScraper:
    def __init__(self, base_url='https://www.pref.miyagi.jp/life/4/15/49/index.html'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        })
        # メタデータを保存するJSONファイル
        self.metadata_file = 'miyagi_river_metadata.json'
        # 今日の日付をファイル名に使用
        today = datetime.datetime.now().strftime("%Y%m%d")
        self.new_articles_csv = f'new_river_articles_{today}.csv'

    def fetch_page(self):
        """ページを取得してBeautifulSoupオブジェクトを返す"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"ページの取得に失敗しました: {e}")
            return None

    def extract_articles(self, soup):
        """記事情報を抽出する"""
        if not soup:
            return []

        articles = []
        content_div = soup.find('div', id='tmp_contents')
        if not content_div:
            print("コンテンツ領域が見つかりませんでした")
            return []

        ul_element = content_div.find('ul')
        if not ul_element:
            print("記事リストが見つかりませんでした")
            return []

        for li in ul_element.find_all('li'):
            try:
                # リンク要素を取得
                link = li.find('a')
                if not link:
                    continue
                
                # テキスト全体を取得して解析
                full_text = li.get_text().strip()
                
                # 日付を正規表現で抽出 (YYYY年MM月DD日 の形式)
                date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', full_text)
                if date_match:
                    year = int(date_match.group(1))
                    month = int(date_match.group(2))
                    day = int(date_match.group(3))
                    
                    # 日付文字列の形式
                    date_str = f"{year}年{month}月{day}日"
                    
                    # 数値形式の日付（YYYYMMDD）
                    date_value = year * 10000 + month * 100 + day
                    
                    # タイトルはリンクのテキスト
                    title = link.get_text().strip()
                    
                    # URL
                    url = urljoin(self.base_url, link['href'])
                    
                    articles.append({
                        'date_str': date_str,
                        'date_value': date_value,
                        'title': title,
                        'url': url
                    })
                else:
                    print(f"日付パターンが見つかりませんでした: {full_text[:30]}...")
            except Exception as e:
                print(f"記事の抽出中にエラーが発生しました: {e}")

        # 日付の新しい順にソート
        articles.sort(key=lambda x: x['date_value'], reverse=True)
        return articles
    
    def load_metadata(self):
        """メタデータをロードする"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"メタデータのロード中にエラーが発生しました: {e}")
                return self.create_default_metadata()
        return self.create_default_metadata()
    
    def create_default_metadata(self):
        """デフォルトのメタデータを作成"""
        now = datetime.datetime.now()
        return {
            "last_date_value": 0,  # 最後にスクレイピングした記事の日付値
            "last_run": now.strftime("%Y-%m-%d %H:%M:%S"),  # 最後の実行日時
            "total_articles_found": 0,  # これまでに見つけた記事の総数
            "total_new_articles": 0,  # これまでに見つけた新しい記事の総数
            "execution_history": [],  # 実行履歴
            "source_url": self.base_url  # ソースURL
        }
    
    def save_metadata(self, metadata):
        """メタデータを保存する"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"メタデータの保存中にエラーが発生しました: {e}")
    
    def update_metadata(self, metadata, articles, new_articles):
        """メタデータを更新する"""
        now = datetime.datetime.now()
        
        # 最新の記事日付を更新（記事がある場合のみ）
        if articles:
            metadata["last_date_value"] = articles[0]["date_value"]
        
        # 最終実行日時を更新
        metadata["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 累計の記事数を更新
        metadata["total_articles_found"] += len(articles)
        metadata["total_new_articles"] += len(new_articles)
        
        # 実行履歴に追加（最新10件のみ保持）
        execution_record = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "articles_found": len(articles),
            "new_articles": len(new_articles)
        }
        metadata["execution_history"].insert(0, execution_record)
        metadata["execution_history"] = metadata["execution_history"][:10]  # 最新10件のみ
        
        return metadata
    
    def find_new_articles(self, articles, last_date_value):
        """前回の最新日付より新しい記事を抽出する"""
        return [article for article in articles if article['date_value'] > last_date_value]
    
    def save_to_csv(self, articles, filename):
        """記事情報をCSVファイルに保存する"""
        if not articles:
            print(f"保存する記事がありません: {filename}")
            return False

        try:
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date_str', 'title', 'url'])
                writer.writeheader()
                for article in articles:
                    # date_valueフィールドを除外
                    row = {
                        'date_str': article['date_str'],
                        'title': article['title'],
                        'url': article['url']
                    }
                    writer.writerow(row)
            print(f"{len(articles)}件の記事を {filename} に保存しました")
            return True
        except Exception as e:
            print(f"CSVファイルの保存中にエラーが発生しました: {e}")
            return False

    def run(self):
        """スクレイピングを実行する"""
        print(f"宮城県河川情報ページのスクレイピングを開始します...")
        
        # メタデータをロード
        metadata = self.load_metadata()
        last_date_value = metadata.get("last_date_value", 0)
        print(f"前回の最新記事日付: {last_date_value}")
        
        # 現在のデータを取得
        soup = self.fetch_page()
        articles = self.extract_articles(soup)
        
        if articles:
            print(f"{len(articles)}件の記事が見つかりました")
            
            # 最新の記事日付を取得（ソート済みなので先頭の記事）
            latest_date = articles[0]['date_value']
            print(f"現在の最新記事日付: {latest_date}")
            
            # 新しい記事を見つける
            new_articles = self.find_new_articles(articles, last_date_value)
            print(f"そのうち{len(new_articles)}件が新しい記事です")
            
            # 新しい記事があれば保存
            if new_articles:
                self.save_to_csv(new_articles, self.new_articles_csv)
            else:
                print("新しい記事はありませんでした")
            
            # メタデータを更新して保存
            updated_metadata = self.update_metadata(metadata, articles, new_articles)
            self.save_metadata(updated_metadata)
            
            return new_articles
        else:
            print("記事が見つかりませんでした")
            # 記事が見つからなくても、実行記録は残す
            updated_metadata = self.update_metadata(metadata, [], [])
            self.save_metadata(updated_metadata)
            return []

if __name__ == "__main__":
    # スクレイパーを初期化して実行
    scraper = MiyagiRiverScraper()
    new_articles = scraper.run()
    
    # 新しい記事があれば出力
    if new_articles:
        print("\n新しい記事:")
        for article in new_articles:
            print(f"{article['date_str']} - {article['title']}")
            print(f"URL: {article['url']}\n")