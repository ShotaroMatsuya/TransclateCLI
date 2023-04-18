# Transcrate CLI

`Transcrate とは、transcribe + translate の造語`

1. 動画ファイルを文字起こしし、
2. 複数言語(日本語、英語、スペイン語、中国語、韓国語、ポルトガル語、ドイツ語、フランス語に対応)に翻訳し、
3. closed caption として動画に埋め込む
   機能をもつ CLI アプリケーションのサンプル

## Prerequisite

- python3
- AWS アカウント
- boto3
- アウトプット用 S3 バケット
- IAM 権限(amazon translate, amazon S3, amazon transcribe へのアクセス権限)
- mp4 形式の動画ファイル
  など

## CLI コマンド

## アーキテクチャ
