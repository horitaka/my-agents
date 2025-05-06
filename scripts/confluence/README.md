# Confluence Cloud API スクリプト

このディレクトリには、Confluence Cloud API を利用するためのPythonスクリプトが含まれています。

## 必要条件

- Python 3.6以上
- 以下のPythonパッケージ:
  - requests
  - python-dotenv

パッケージのインストール:

```bash
pip install requests python-dotenv
```

## 環境設定

1. `.env`ファイルをプロジェクトのルートディレクトリに作成し、以下の情報を設定してください：

```
CONFLUENCE_DOMAIN=your-domain.atlassian.net
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_EMAIL=your-email@example.com
```

## スクリプト一覧

### get_page.py

Confluence Cloud REST API v2 を使用して特定のページ情報を取得します。

#### 使い方

##### 環境変数を使用する場合:

```bash
# confluenceディレクトリ内で実行する場合
python get_page.py --page-id <PAGE_ID>

# プロジェクトルートから実行する場合
python confluence/get_page.py --page-id <PAGE_ID>
```

##### コマンドライン引数で認証情報を指定する場合:

```bash
# confluenceディレクトリ内で実行する場合
python get_page.py --domain <DOMAIN> --token <API_TOKEN> --email <EMAIL> --page-id <PAGE_ID>

# プロジェクトルートから実行する場合
python confluence/get_page.py --domain <DOMAIN> --token <API_TOKEN> --email <EMAIL> --page-id <PAGE_ID>
```

#### 引数の説明

- `--domain`: Confluenceドメイン (例: your-domain.atlassian.net)
- `--token`: Confluence API トークン
- `--email`: Confluenceアカウントのメールアドレス
- `--page-id`: 取得するページのID (必須)

#### 出力

取得したページ情報をJSON形式で標準出力に表示します。

## API トークンの取得方法

1. Atlassian アカウントにログイン: https://id.atlassian.com/manage-profile/security/api-tokens
2. 「APIトークンの作成」をクリック
3. トークンのラベルを入力し、「作成」をクリック
4. 生成されたトークンを`.env`ファイルの`CONFLUENCE_API_TOKEN`に設定 