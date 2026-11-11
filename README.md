# ぜんにゅー | NYU NETWORK

公式サイト（設定予定）：https://zen.nyu-net.jp/

本リポジトリは「ぜんにゅー」の公開サイト専用です。HTML/CSS/JSをリポジトリ直下に配置し、GitHub Pages の `main` / `/(root)` から公開します。

## 管理・公開の分担

- **共通基盤と管理画面:** [nyu-network](https://github.com/blacksmith-tombokiri/nyu-network)
- **公開用フロントエンドの原本:** `nyu-network/zennyu/`
- **このリポジトリ:** GitHub Pages 配信先。管理画面や秘密情報を含めません。

## 自動同期

[Sync public ぜんにゅー site](.github/workflows/sync-public-site.yml) により、毎時17分に親リポジトリの `main/zennyu/` から公開用HTML/CSS/JSを同期します。必要な場合は Actions の `Run workflow` から手動同期できます。

`CNAME`、`.nojekyll`、`.github/`、`README.md` は同期処理から保護されます。GitHub Actions に `contents: write` が許可されている必要があります。

## 独自ドメイン移行

1. 本リポジトリの **Settings → Pages** で `Deploy from a branch` / `main` / `/(root)` を指定。
2. 旧 `nyu-network` 側の Pages から `zen.nyu-net.jp` の Custom domain を解除。
3. 本リポジトリの Pages で `zen.nyu-net.jp` を登録し、DNS検証後に `Enforce HTTPS` を有効化。
4. さくら側の `zen` の CNAME（`blacksmith-tombokiri.github.io.`）はそのまま維持。

この操作で親サイトのコードや管理画面は変更されません。
