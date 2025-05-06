#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import argparse
import os
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv


def get_page_by_id(domain, api_token, email, page_id):
    """
    Confluence Cloud REST API v2を使ってページIDからページを取得する

    Args:
        domain: Confluenceドメイン (例: 'your-domain.atlassian.net')
        api_token: Confluenceのapi token
        email: Confluenceアカウントのメールアドレス
        page_id: 取得するページのID

    Returns:
        取得したページ情報（JSON）
    """
    url = f"https://{domain}/wiki/api/v2/pages/{page_id}"

    auth = HTTPBasicAuth(email, api_token)

    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code != 200:
        print(f"エラー: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json()


def main():
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # 環境変数から認証情報を取得
    domain = os.getenv("CONFLUENCE_DOMAIN")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    email = os.getenv("CONFLUENCE_EMAIL")

    parser = argparse.ArgumentParser(
        description="Confluence Cloud REST API v2でページを取得する"
    )
    parser.add_argument(
        "--domain",
        help="Confluenceドメイン (例: your-domain.atlassian.net)",
    )
    parser.add_argument("--token", help="APIトークン")
    parser.add_argument("--email", help="Confluenceアカウントのメールアドレス")
    parser.add_argument("--page-id", required=True, help="取得するページのID")

    args = parser.parse_args()

    # コマンドラインの引数があれば、環境変数の値を上書き
    if args.domain:
        domain = args.domain
    if args.token:
        api_token = args.token
    if args.email:
        email = args.email

    # 必須パラメータのチェック
    if not domain:
        print(
            "エラー: Confluenceドメインが指定されていません。.envファイルまたは--domainオプションで指定してください。"
        )
        sys.exit(1)
    if not api_token:
        print(
            "エラー: APIトークンが指定されていません。.envファイルまたは--tokenオプションで指定してください。"
        )
        sys.exit(1)
    if not email:
        print(
            "エラー: メールアドレスが指定されていません。.envファイルまたは--emailオプションで指定してください。"
        )
        sys.exit(1)

    result = get_page_by_id(domain, api_token, email, args.page_id)

    # 結果を整形して表示
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
