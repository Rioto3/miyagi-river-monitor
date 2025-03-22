# 宮城県河川情報通知システム

## 概要

このプロジェクトは宮城県の河川情報ページから最新情報を定期的にスクレイピングし、新しい情報が公開されたときにLINE通知を送信するシステムです。特に、木材の無料配布などの有益な情報をタイムリーにキャッチすることを目的としています。

## 特徴

- 宮城県の河川情報ページから最新情報を自動収集
- 前回のチェック以降に新しく掲載された情報のみを検出
- 新しい情報がある場合のみLINE通知を送信
- GitHub Actionsで毎日定期実行（日本時間 午前9時）

## 仕組み

1. GitHub Actionsで定期的にスクレイピングスクリプトを実行
2. 前回のチェック以降に新しく掲載された情報を検出
3. 新しい情報があれば、LINE通知用のテキストを生成
4. LINE通知APIを使用して該当情報を送信

## セットアップ方法

### リポジトリのクローン

```bash
git clone https://github.com/yourusername/miyagi-river-info.git
cd miyagi-river-info
```

### 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 通知設定

通知にはLINE送信用のAPIが必要です。このリポジトリではGoogle Apps Script（GAS）を使用した自作のAPI連携を使用していますが、フォークして使用する場合は各自で通知手段を準備してください。

1. GitHub Secretsに以下の値を設定する必要があります：
   - `MAKANA_LINE_API_KEY`: LINE通知用APIキー
   - `MAKANA_CALL_URL`: LINE通知送信先のURL
   - `GHUB_TOKEN`: GitHubリポジトリ操作用のアクセストークン

### GitHub Actionsの設定

このプロジェクトは自動的に毎日実行されますが、手動実行も可能です：

1. リポジトリの「Actions」タブにアクセス
2. 「宮城県河川情報スクレイピング」ワークフローを選択
3. 「Run workflow」ボタンをクリック

## ファイル構成

- `scraper.py`: スクレイピングと通知テキスト生成を行うメインスクリプト
- `.github/workflows/makana-send.yml`: GitHub Actions定義ファイル
- `miyagi_river_metadata.json`: 最終実行状態を保存するメタデータファイル
- `notification_output.txt`: 通知用テキスト出力ファイル
- `requirements.txt`: 必要なPythonパッケージ一覧

## カスタマイズ

### 通知間隔の変更

`.github/workflows/makana-send.yml`のcron設定を変更することで、実行間隔を調整できます：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # UTC 0:00 (日本時間 午前9時)
```

### 通知形式の変更

`scraper.py`の`generate_notification_text`メソッドを編集することで、通知メッセージの形式をカスタマイズできます。

## フォークして使用する場合

このプロジェクトをフォークして使用する際は、以下の点に注意してください：

1. LINE通知の部分は独自に実装する必要があります
2. スクレイピング対象サイトへの負荷を考慮し、実行頻度を適切に設定してください
3. GitHubの利用規約およびスクレイピング対象サイトの利用規約を遵守してください
