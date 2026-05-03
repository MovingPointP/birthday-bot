# 誕生日通知Bot 仕様書

## 概要

Firestoreに登録された誕生日情報をもとに、毎日0時にDiscord Webhookへ通知を送るBot。

---

## アーキテクチャ

```
Cloud Scheduler（毎日0時 JST）
    ↓
Cloud Functions（Python）
    ↓
Firestore（誕生日データ参照）
    ↓
Discord Webhook（通知送信）
```

---

## 使用サービス

| サービス | 用途 | 料金 |
|---|---|---|
| Cloud Scheduler | 毎日0時にFunctionsをトリガー | 無料（3ジョブ/アカウントまで） |
| Cloud Functions | 誕生日チェック・通知処理 | 無料（200万回/月まで） |
| Firestore | 誕生日データの保存 | 無料（デフォルトDB1つ） |

---

## Firestoreデータ構造

### データベース設定

| 項目 | 値 |
|---|---|
| データベースID | `(default)` |
| エディション | Standard Edition |
| モード | Firestore in Native mode |
| リージョン | asia-northeast1（東京） |
| セキュリティルール | 限定的（全拒否） |

### コレクション・ドキュメント構造

```
birthdays/                    ← コレクション
└── {自動ID}/                 ← ドキュメント（1人1ドキュメント）
    ├── name  : string  ※必須  例: "田中太郎"
    ├── month : number  ※必須  例: 5
    ├── day   : number  ※必須  例: 2
    └── note  : string  ※任意  例: "ケーキ🎂"
```

### 誕生日の登録方法

GCPコンソールのFirestore画面から手動でドキュメントを追加する。

---

## Cloud Functions

| 項目 | 値 |
|---|---|
| ランタイム | Python 3.12 |
| トリガー | Cloud Scheduler（HTTP） |
| リージョン | asia-northeast1（東京） |

### 環境変数

| 変数名 | 説明 |
|---|---|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |

### 処理フロー

1. Cloud SchedulerからHTTPリクエストを受信
2. Firestoreの `birthdays` コレクションから本日の月・日が一致するドキュメントを取得
3. 該当者が1人以上いる場合、Discord Webhookに通知を送信
4. 該当者がいない場合は何もしない

---

## Cloud Scheduler

| 項目 | 値 |
|---|---|
| 実行頻度 | 毎日0時（JST） |
| Cron式 | `0 15 * * *`（UTC 15時 = JST 0時） |
| タイムゾーン | Asia/Tokyo |
| ターゲット | Cloud Functions（HTTP） |

---

## Discord通知

### 通知条件

- 当日が誕生日の人が1人以上いる場合のみ通知
- 誕生日の人が複数いる場合は1人ずつメッセージを送信

### メッセージフォーマット

例

```
🎂 今日は {name} の誕生日です！おめでとう！🎉
```

`note` が設定されている場合：

```
🎂 今日は {name} の誕生日です！おめでとう！🎉
📝 {note}
```

### 通知チャンネル

Discord Webhook URL 1つ（Cloud Functionsの環境変数で管理）

---

## セキュリティ

- Discord Webhook URLはコードに直接記載せず、**Cloud Functionsの環境変数**で管理
- FirestoreへのアクセスはCloud FunctionsのAdmin SDKのみ（セキュリティルールをバイパス）
- Cloud FunctionsのエンドポイントはCloud Schedulerからのみ呼び出し可能とする（`--no-allow-unauthenticated`）

---

## デプロイ

```bash
gcloud functions deploy birthday-notify \
  --gen2 \
  --runtime python312 \
  --region asia-northeast1 \
  --source . \
  --entry-point birthday_notify \
  --trigger-http \
  --no-allow-unauthenticated \
  --env-vars-file .env.yaml
```

`.env.yaml` の `DISCORD_WEBHOOK_URL` に実際のWebhook URLを設定してからデプロイする。

---

## 今後の拡張候補（現時点では対象外）

- 数日前の事前通知
