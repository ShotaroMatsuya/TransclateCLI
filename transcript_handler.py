import os
import time
from logging import DEBUG, Formatter, StreamHandler, getLogger
import boto3
from helper.aws_sdk_helper import S3Helper
from halo import Halo
import click

spinner = Halo(text="Loading", spinner="dots", color="magenta", text_color="cyan")
logger = getLogger("[Transcribe]")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

transcribe = boto3.client("transcribe", region_name="us-east-1")
bucket_for_input = "smat-transcription-input"


def check_job_name(job_name):
    """job名の重複を確認"""
    spinner.start("ジョブ名の重複を確認 ::{}".format(job_name))
    job_verification = True
    # all the transcriptions
    existed_jobs = transcribe.list_transcription_jobs(
        JobNameContains=job_name, MaxResults=20
    )
    for job in existed_jobs["TranscriptionJobSummaries"]:
        if job_name == job["TranscriptionJobName"]:
            job_verification = False
            break
    if job_verification is False:
        command = click.prompt(
            job_name + " has existed. \nDo you want to override the existed job (Y/N): "
        )
        if command.lower() == "y" or command.lower() == "yes":
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        elif command.lower() == "n" or command.lower() == "no":
            job_name = click.prompt("Insert new job name? ")
            check_job_name(job_name)
        else:
            print("Input can only be (Y/N)")
            command = click.prompt(
                job_name
                + " has existed. \nDo you want to override the existed job (Y/N): "
            )
    spinner.succeed("ジョブ名の重複を確認 ::{}".format(job_name))
    return job_name


def amazon_transcribe(audio_file_name, src_lang):
    """ローカルファイルを指定してtranscribeを実行"""
    file_name = os.path.basename(audio_file_name)
    # 存在check
    if os.path.exists(os.path.join(os.path.dirname(__file__), audio_file_name)):
        spinner.info("ローカルファイル「%s」は存在します。" % (audio_file_name))
    else:
        spinner.fail("ローカルファイル「%s」は存在しません。" % (audio_file_name))
        return False
    spinner.start("メディアファイルのアップロード開始 ::{}".format(audio_file_name))
    # Upload audio_file
    S3Helper().uploadToS3(bucket_for_input, "transcribe-input", audio_file_name)
    spinner.succeed("メディアファイルのアップロード完了 ::{}".format(audio_file_name))

    job_uri = "s3://{}/transcribe-input/{}".format(bucket_for_input, file_name)

    job_name = src_lang + "." + (file_name.split(".")[0]).replace(" ", "")
    file_format = file_name.split(".")[1]

    # Set Language
    if src_lang == "ja":  # 日本語
        lang_code = "ja-JP"
    elif src_lang == "en":  # 英語
        lang_code = "en-US"
    elif src_lang == "es":  # スペイン語
        lang_code = "es-US"
    elif src_lang == "zh":  # 中国語
        lang_code = "zh-CN"
    elif src_lang == "ko":  # 韓国語
        lang_code = "ko-KR"
    elif src_lang == "pt":  # ポルトガル語
        lang_code = "pt-BR"
    elif src_lang == "de":  # ドイツ語
        lang_code = "de-DE"
    elif src_lang == "fr":  # フランス語
        lang_code = "fr-FR"

    # check if name is taken or not
    job_name = check_job_name(job_name)

    spinner.start("Transcribe Jobの開始 ::{}".format(job_name))
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": job_uri},
        MediaFormat=file_format,
        LanguageCode=lang_code,  # 日本語：ja-JP
        OutputBucketName=bucket_for_input,
        OutputKey="transcribe-output/",
        Subtitles={"Formats": ["vtt"]},
    )

    check_status_of_job(job_name)
    spinner.succeed("Transcribe Jobの完了 ::{}".format(job_name))
    transcribe.delete_transcription_job(TranscriptionJobName=job_name)


def check_status_of_job(job_name):
    while True:
        result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if result["TranscriptionJob"]["TranscriptionJobStatus"] in [
            "COMPLETED",
            "FAILED",
        ]:
            break
        time.sleep(15)
    if result["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
        transcript_output = result["TranscriptionJob"]["Transcript"][
            "TranscriptFileUri"
        ]
        subtitle_output = result["TranscriptionJob"]["Subtitles"]["SubtitleFileUris"][0]
        transcript_file_name = os.path.split(transcript_output)[1]  # .(mp4)
        subtitle_file_name = os.path.split(subtitle_output)[1]  # .vtt
        spinner.start("{}をダウンロード開始".format(transcript_file_name))
        S3Helper().downloadFromS3(
            bucket_for_input,
            "transcribe-output/{}".format(transcript_file_name),
            transcript_file_name,
        )
        spinner.start("{}をダウンロード開始".format(subtitle_file_name))
        S3Helper().downloadFromS3(
            bucket_for_input,
            "transcribe-output/{}".format(subtitle_file_name),
            subtitle_file_name,
        )

        S3Helper().deleteObject(
            bucket_for_input, "transcribe-output/{}".format(transcript_file_name)
        )
        S3Helper().deleteObject(
            bucket_for_input, "transcribe-output/{}".format(subtitle_file_name)
        )
        spinner.succeed("{}をダウンロード完了".format(transcript_file_name))
        spinner.succeed("{}をダウンロード完了".format(subtitle_file_name))
        
        
def main():
    amazon_transcribe("Usage-of-S3-Buckets.mp4", "en")
    logger.info("transcribe job完了")


if __name__ == "__main__":
    main()
