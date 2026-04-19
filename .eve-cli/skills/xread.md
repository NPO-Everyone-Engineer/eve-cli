---
description: "ユーザーが X の公開情報を取得したいとき、xurl を使って検索・ポスト取得・ユーザー投稿取得を行いたいとき（例: 「Xで検索して」「このアカウントの最近の投稿を見て」「このポストを取得して」）"
allowed-tools: [Bash]
---
# X Read Only

## 目的
`xurl` を使って X API から公開情報を read-only で取得する。
投稿・削除・更新などの write 操作は行わない。

## 前提
- `xurl` が PATH にあること
- `xurl` の認証設定が済んでいること
- X API の read 権限が有効なこと

## 安全ルール
- `-X POST`, `-X DELETE`, `-X PUT`, `-X PATCH` は使わない
- `POST /2/tweets` など書き込み系 endpoint は使わない
- まず取得用途を短く確認し、適切な endpoint を選ぶ

## 代表的な使い方

### 1. キーワードで最近の投稿を検索
```bash
xurl "/2/tweets/search/recent?query=<QUERY>&max_results=10&tweet.fields=created_at,author_id,public_metrics&expansions=author_id&user.fields=username,name"
```

### 2. ユーザー名から user 情報を取得
```bash
xurl "/2/users/by/username/<USERNAME>?user.fields=description,created_at,public_metrics,verified"
```

### 3. ユーザー ID の最近の投稿を取得
```bash
xurl "/2/users/<USER_ID>/tweets?max_results=10&tweet.fields=created_at,public_metrics"
```

### 4. 特定ポストを取得
```bash
xurl "/2/tweets/<POST_ID>?tweet.fields=created_at,author_id,public_metrics&expansions=author_id&user.fields=username,name"
```

## 実行手順
1. ユーザー要求を次のどれかに分類する:
   - 検索
   - ユーザー lookup
   - ユーザー投稿一覧
   - 単一ポスト lookup
2. `xurl` で read-only endpoint を実行する
3. 必要なら JSON を整形するため `python3 -m json.tool` を使う
4. 結果は要点を日本語で要約し、必要なら raw JSON の重要フィールドも抜き出す

## 注意
- ユーザー名から投稿一覧を取るときは、先に `users/by/username` で user ID を引く
- レート制限や認証エラーが出たら、そのままメッセージを要約して返す
- `xurl` が見つからない場合は、インストールまたは PATH 設定不足として報告する
