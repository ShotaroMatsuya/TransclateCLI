# Transclate CLI
```bash
Create Transcription in various languages and Embed it as Subtitles in Movies (powered by AWS AI services)
  ______                           __      __          ________    ____
 /_  __/________ _____  __________/ /___ _/ /____     / ____/ /   /  _/
  / / / ___/ __ `/ __ \/ ___/ ___/ / __ `/ __/ _ \   / /   / /    / /  
 / / / /  / /_/ / / / (__  ) /__/ / /_/ / /_/  __/  / /___/ /____/ /   
/_/ /_/   \__,_/_/ /_/____/\___/_/\__,_/\__/\___/   \____/_____/___/   
                                                                       
```

`Transclate とは、transcribe + translate の造語`

1. 動画ファイルを文字起こしし、
2. 複数言語(日本語、英語、スペイン語、中国語、韓国語、ポルトガル語、ドイツ語、フランス語に対応)に翻訳し、
3. closed caption として動画に埋め込む  
   機能をもつ CLI アプリケーションのサンプル

## Requirement

- Prerequisite
  1. pip
  2. boto3

To Install boto3 the SDK Package for python using pip cmd as mentioned below

```bash
pip install boto3 --user
```
```bash
# Step1: Update and upgrade Homebrew Formulae
brew update
brew upgrade
# Step2: Install FFmpeg
brew install ffmpeg
```

- python v3.8
- 個人のAWS アカウント
- boto3
- アウトプット用 S3 バケット
- IAM 権限(amazon translate, amazon S3, amazon transcribe へのアクセス権限)
- mp4 形式の動画ファイル
  などなど

## CLI コマンド

### 基本コマンド
```bash
Usage: transclate [OPTIONS] COMMAND [ARGS]...

  Transcrate CLI

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  info              Info About CLI
  start-all         Create Transcription in various languages and Embed...
  start-embed
  start-transcribe
  start-translate
```
### サブコマンド (start-all)
```bash
Usage: transclate start-all [OPTIONS] MEDIA_FILE

  Create Transcription in various languages and Embed it as Subtitles in
  Movies (powered by AWS AI services)

Options:
  -n, --native [ja|en|ko|zh|es|pt|de|fr]
                                  Option to select the speaker's native
                                  language (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語,
                                  es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)
  --help                          Show this message and exit.
```
### サブコマンド(start-embed)
```bash
Usage: transclate start-embed [OPTIONS] MEDIA_FILE

Options:
  --help  Show this message and exit.
```
### サブコマンド(start-transcribe)
```bash
Usage: transclate start-transcribe [OPTIONS] MEDIA_FILE

Options:
  -n, --native [ja|en|ko|zh|es|pt|de|fr]
                                  select the speaker's native (ja: 日本語, en:
                                  英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語,
                                  de:ドイツ語, fr: フランス語)
  --help                          Show this message and exit.
```
### サブコマンド(start-translate)
```bash
Usage: transclate start-translate [OPTIONS] [VTT_FILE]

Options:
  --help  Show this message and exit.
```

### 
## アーキテクチャ
