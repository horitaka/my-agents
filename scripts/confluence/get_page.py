#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import argparse
import os
import re
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from bs4 import BeautifulSoup


def convert_storage_to_markdown(storage_content):
    """
    Confluenceのstorageフォーマット（XHTML-based）をMarkdownに変換する

    Args:
        storage_content: Confluenceのstorageフォーマットの内容

    Returns:
        変換されたMarkdownテキスト
    """
    soup = BeautifulSoup(storage_content, "html.parser")

    # Confluence特有のマクロを処理（先に処理する）
    # コードブロックマクロ
    for macro in soup.find_all(["ac:structured-macro"]):
        macro_name = macro.get("ac:name", "")

        if macro_name == "code":
            language = ""
            for param in macro.find_all("ac:parameter"):
                if param.get("ac:name") == "language":
                    language = param.get_text().strip()

            code_body = macro.find("ac:plain-text-body")
            if code_body:
                code_text = code_body.get_text()
                code_block = soup.new_tag("pre")
                code_element = soup.new_tag("code")
                if language:
                    code_element["class"] = f"language-{language}"
                code_element.string = code_text
                code_block.append(code_element)
                macro.replace_with(code_block)

        elif macro_name == "panel":
            panel_type = ""
            for param in macro.find_all("ac:parameter"):
                if param.get("ac:name") == "type":
                    panel_type = param.get_text().strip()

            rich_text = macro.find("ac:rich-text-body")
            if rich_text:
                panel_content = rich_text.get_text().strip()
                panel_div = soup.new_tag("div")
                panel_div["class"] = f"panel {panel_type}"
                panel_div.string = panel_content
                macro.replace_with(panel_div)

        # インラインコメント
        elif macro_name == "inline-comment":
            comment_text = ""
            rich_text = macro.find("ac:rich-text-body")
            if rich_text:
                comment_text = rich_text.get_text().strip()
            macro.replace_with(comment_text)

        # その他のマクロはできるだけテキスト抽出
        else:
            rich_text = macro.find("ac:rich-text-body")
            if rich_text:
                text_content = rich_text.get_text().strip()
                macro.replace_with(text_content)
            else:
                plain_text = macro.find("ac:plain-text-body")
                if plain_text:
                    text_content = plain_text.get_text().strip()
                    macro.replace_with(text_content)
                else:
                    # マクロのテキスト全体を抽出
                    text_content = macro.get_text().strip()
                    macro.replace_with(text_content)

    # 見出し変換
    for i in range(1, 7):
        for h in soup.find_all(f"h{i}"):
            text = h.get_text().strip()
            h.replace_with(f"{'#' * i} {text}\n\n")

    # 段落変換
    for p in soup.find_all("p"):
        text = p.get_text().strip()
        if text:
            p.replace_with(f"{text}\n\n")
        else:
            p.replace_with("\n")

    # 強調・太字
    for strong in soup.find_all(["strong", "b"]):
        text = strong.get_text()
        strong.replace_with(f"**{text}**")

    for em in soup.find_all(["em", "i"]):
        text = em.get_text()
        em.replace_with(f"*{text}*")

    # リスト変換
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li", recursive=False):
            text = li.get_text().strip()
            li.replace_with(f"* {text}\n")

    for ol in soup.find_all("ol"):
        for i, li in enumerate(ol.find_all("li", recursive=False), 1):
            text = li.get_text().strip()
            li.replace_with(f"{i}. {text}\n")

    # コードブロック
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        if code:
            language = ""
            if code.get("class"):
                for cls in code.get("class"):
                    if cls.startswith("language-"):
                        language = cls.replace("language-", "")
                        break

            code_text = code.get_text()
            pre.replace_with(f"```{language}\n{code_text}\n```\n\n")
        else:
            text = pre.get_text()
            pre.replace_with(f"```\n{text}\n```\n\n")

    # インラインコード
    for code in soup.find_all("code"):
        if code.parent.name != "pre":  # プリフォーマットの子要素でない場合のみ
            text = code.get_text()
            code.replace_with(f"`{text}`")

    # リンク変換
    for a in soup.find_all("a"):
        text = a.get_text()
        href = a.get("href", "")
        a.replace_with(f"[{text}]({href})")

    # テーブル変換（基本的な変換）
    for table in soup.find_all("table"):
        markdown_table = []
        headers = []

        # テーブルヘッダー処理
        for th in table.find_all("th"):
            headers.append(th.get_text().strip())

        if headers:
            markdown_table.append("| " + " | ".join(headers) + " |")
            separator = ["---"] * len(headers)
            markdown_table.append("| " + " | ".join(separator) + " |")

        # テーブル行処理
        for tr in table.find_all("tr"):
            row = []
            # th要素も取得（ヘッダーじゃない行にもth要素がある場合）
            cells = tr.find_all(["td", "th"])

            if cells:
                for cell in cells:
                    row.append(cell.get_text().strip())
                markdown_table.append("| " + " | ".join(row) + " |")

        if markdown_table:
            table_text = "\n".join(markdown_table) + "\n\n"
            table.replace_with(table_text)

    # 引用
    for blockquote in soup.find_all("blockquote"):
        text = blockquote.get_text().strip()
        lines = text.split("\n")
        quoted_lines = []
        for line in lines:
            quoted_lines.append(f"> {line}")
        blockquote.replace_with("\n".join(quoted_lines) + "\n\n")

    # 水平線
    for hr in soup.find_all("hr"):
        hr.replace_with("\n---\n\n")

    # 画像
    for img in soup.find_all("img"):
        alt_text = img.get("alt", "")
        src = img.get("src", "")
        img.replace_with(f"![{alt_text}]({src})")

    # Confluence特有の参照・添付ファイル
    for ri in soup.find_all("ri:attachment"):
        filename = ri.get("ri:filename", "")
        if filename:
            ri.replace_with(f"[添付ファイル: {filename}]")

    for ri in soup.find_all("ri:page"):
        page_title = ri.get("ri:content-title", "")
        if page_title:
            ri.replace_with(f"[ページ: {page_title}]")

    # すべての処理後の最終テキストを取得
    result = soup.get_text()

    # 余分な空白行を削除
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


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
    url = f"https://{domain}/wiki/api/v2/pages/{page_id}?body-format=storage"

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
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="出力フォーマット (json または markdown)",
    )

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

    if args.format == "json":
        # 結果を整形して表示
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:  # markdown
        if (
            "body" in result
            and "storage" in result["body"]
            and "value" in result["body"]["storage"]
        ):
            storage_content = result["body"]["storage"]["value"]
            markdown_text = convert_storage_to_markdown(storage_content)
            print(f"title: {result['title']}\n\n{markdown_text}")
        else:
            print("エラー: ページの内容が取得できませんでした。")
            sys.exit(1)


if __name__ == "__main__":
    main()
