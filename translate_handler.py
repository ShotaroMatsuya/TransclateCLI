import os
import time
from pathlib import Path

from logging import DEBUG, Formatter, StreamHandler, getLogger

# from pathlib import Path
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from helper.captions_and_srt_converter import Captions
from helper.aws_sdk_helper import AwsHelper, FileHelper, S3Helper
from halo import Halo

spinner = Halo(text="Loading", spinner="dots", color="magenta", text_color="cyan")

logger = getLogger("[Translate]")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
translate_bucket_name = "smat-transcription-input"
aws_account_id = "528163014577"
iam_role_arn = f"arn:aws:iam::{aws_account_id}:role/TranslateCaptionServiceRole"


def createDelimitedCaptions(src_vtt):
    try:
        captions = Captions()
        # filter only the VTT for processing in the input folder
        objs = S3Helper().getFilteredFileNames(
            translate_bucket_name, "translate-input/", ["vtt"]
        )
        for obj in objs:
            vttObject = {}
            vttObject["Bucket"] = translate_bucket_name
            vttObject["Key"] = obj
            captions_list = []
            # based on the file type call the method that converts them into python list object
            spinner.info("vttをweb captionに変換開始")
            if obj.endswith("vtt"):
                captions_list = captions.vttToCaptions(vttObject)
            # spanタグで区切る
            delimitedFile = captions.ConvertToDemilitedFiles(captions_list)
            spinner.info("vttをcaptionに変換完了")
            spinner.start("delimitedファイルをS3にupload開始")
            fileName = os.path.basename(src_vtt)
            newObjectKey = "captions-in/{}.delimited".format(fileName)
            S3Helper().writeToS3(
                str(delimitedFile), translate_bucket_name, newObjectKey
            )
            S3Helper().renameObject(
                translate_bucket_name, obj, "{}.processed".format(obj)
            )
            spinner.succeed("delimitedファイルをS3にupload完了")
    except ClientError as e:
        spinner.fail("An error occurred with S3 Bucket Operation: %s" % e)
        return None
    
    
def registerJobForDelimitedCaptions(src_lng, target_lng):
    try:
        captions = Captions()
        translateContext = {}
        translateContext["sourceLang"] = src_lng
        translateContext["targetLang"] = target_lng
        translateContext[
            "roleArn"
        ] = iam_role_arn
        translateContext["bucket"] = translate_bucket_name
        translateContext["inputLocation"] = "captions-in/"
        translateContext["outputLocation"] = "captions-out/"
        translateContext["jobPrefix"] = "TranslateJob-captions"
        # Call Amazon Translate to translate the delimited files in the captions-in folder
        jobinfo = captions.TranslateCaptions(translateContext)
        return (jobinfo["JobId"], jobinfo["JobName"])
    except ClientError as e:
        spinner.fail("An error occurred with S3 Bucket Operation: %s" % e)
        return None


def checkStatusOfJob(job_name):
    translate_client = AwsHelper().getClient("translate")
    while True:
        result = translate_client.list_text_translation_jobs(
            Filter={"JobName": job_name}
        )
        if result["TextTranslationJobPropertiesList"][0]["JobStatus"] in [
            "COMPLETED",
            "COMPLETED_WITH_ERROR",
            "FAILED",
        ]:
            break
        time.sleep(15)
    if result["TextTranslationJobPropertiesList"][0]["JobStatus"] == "COMPLETED":
        return True
    else:
        spinner.fail(
            "Job Name {} failed or completed with errors, exiting".format(job_name)
        )
        return False


def convertDelimitedToVtt(job_id):
    """翻訳済みdelimitedファイルを削除 & vttに変換"""
    request = {}
    request["delete_captionsin"] = True
    try:
        translate_client = AwsHelper().getClient("translate")
        response = translate_client.describe_text_translation_job(JobId=job_id)
    except ClientError as e:
        spinner.fail("An error occurred with Amazon Translate Operation: %s" % e)

    up = urlparse(
        response["TextTranslationJobProperties"]["InputDataConfig"]["S3Uri"],
        allow_fragments=False,
    )
    bucketName = up.netloc
    basePrefixPath = "captions-out/" + aws_account_id + "-TranslateText-" + job_id + "/"
    captions = Captions()
    # filter only the delimited files with .delimited suffix
    objs = S3Helper().getFilteredFileNames(bucketName, basePrefixPath, ["delimited"])
    for obj in objs:
        try:
            # Read the Delimited file contents
            content = S3Helper().readFromS3(bucketName, obj)
            fileName = FileHelper().getFileName(obj)
            sourceFileName = FileHelper().getFileName(
                obj.replace(
                    "{}.".format(
                        response["TextTranslationJobProperties"]["TargetLanguageCodes"][
                            0
                        ]
                    ),
                    "",
                )
            )
            sourceFileKey = "translate-input/{}.processed".format(sourceFileName)
            vttObject = {}
            vttObject["Bucket"] = bucketName
            vttObject["Key"] = sourceFileKey
            captions_list = []
            # Based on the file format, call the right method to load the file as python object
            if fileName.endswith("vtt"):
                captions_list = captions.vttToCaptions(vttObject)
            elif fileName.endswith("srt"):
                captions_list = captions.srtToCaptions(vttObject)
            # Replace the text captions with the translated content
            translatedCaptionsList = captions.DelimitedToWebCaptions(
                captions_list, content, "<span>", 15
            )
            translatedText = ""
            # Recreate the Caption files in VTT or SRT format
            if fileName.endswith("vtt"):
                translatedText = captions.captionsToVTT(translatedCaptionsList)

            newObjectKey = "translate-output/{}".format(fileName)
            # Write the VTT or SRT file into the output S3 folder
            S3Helper().writeToS3(str(translatedText), bucketName, newObjectKey)
        except ClientError as e:
            spinner.fail("An error occurred with S3 bucket operations: %s" % e)

    objs = S3Helper().getFilteredFileNames(bucketName, "captions-in/", ["delimited"])
    if request["delete_captionsin"] and request["delete_captionsin"] is True:
        for obj in objs:
            try:
                S3Helper().deleteObject(bucketName, obj)
            except ClientError as e:
                spinner.fail("An error occurred with S3 bucket operations: %s" % e)


def amazon_translate(src_vtt, *target_lang):
    source_language = os.path.basename(src_vtt).split(".")[0]
    # 存在check
    if os.path.exists(os.path.join(os.path.dirname(__file__), "output_dir", src_vtt)):
        spinner.info("ローカルファイル「%s」は存在します" % (src_vtt))
    else:
        spinner.fail("ローカルファイル「%s」は存在しません" % (src_vtt))
        return False
    with Path(f"output_dir/{src_vtt}").open("rb") as fo:
        spinner.start("S3にupload開始 :: {}".format(src_vtt))
        S3Helper.writeToS3(
            fo,
            translate_bucket_name,
            "translate-input/{}".format(os.path.basename(src_vtt)),
        )
        spinner.succeed("S3にupload完了::{}".format(src_vtt))
    createDelimitedCaptions(src_vtt)
    job_list = []  # (JobId,JobName)[]
    for target_language in target_lang:
        job_list.append(
            registerJobForDelimitedCaptions(source_language, target_language)
        )
    for job_id, job_name in job_list:
        spinner.start("translate jobを開始 ::{}".format(job_name))
        if checkStatusOfJob(job_name):
            convertDelimitedToVtt(job_id)
        else:
            spinner.fail(
                "Job ID {} failed or completed with errors, exiting".format(job_id)
            )
        spinner.succeed("translate jobを完了 ::{}".format(job_name))
    for target_language in target_lang:
        # download "ja.*.vtt"
        spinner.start("翻訳済み( {} )のtranscriptをダウンロード開始".format(target_language))
        obj_key = S3Helper().getFilteredFileNames(
            translate_bucket_name,
            "translate-output/{}.{}".format(target_language, os.path.basename(src_vtt)),
            ["vtt"],
        )[0]
        S3Helper().downloadFromS3(
            translate_bucket_name, obj_key, obj_key.split("/")[-1]
        )
        spinner.succeed("翻訳済み( {} )のtranscriptをダウンロード完了".format(target_language))

    processed_captions_obj_key = S3Helper().getFilteredFileNames(
        translate_bucket_name, "translate-input/", ["processed"]
    )[0]
    S3Helper().deleteObject(translate_bucket_name, processed_captions_obj_key)
    spinner.info("翻訳済みcaptionの削除")


def main():
    amazon_translate("en.Usage-of-S3-Buckets.vtt", "ja", "es", "ko")
    logger.info("translate job完了")


if __name__ == "__main__":
    main()
