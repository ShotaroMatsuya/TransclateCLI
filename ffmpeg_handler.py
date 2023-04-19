import os
import subprocess
from logging import DEBUG, Formatter, StreamHandler, getLogger
from halo import Halo

spinner = Halo(text="Loading", spinner="dots", color="magenta", text_color="cyan")

logger = getLogger("[ffmpeg]")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def merge_video_with_vvt(video, *vtt):
    spinner.start()
    video_filepath = os.path.join(os.path.dirname(__file__), video)
    # 存在check
    if os.path.exists(video_filepath):
        spinner.info("ローカルファイル「%s」は存在します。" % (video))
    else:
        spinner.fail("ローカルファイル「%s」は存在しません。" % (video))
        return False

    for val in vtt:
        vtt_filepath = os.path.join(os.path.dirname(__file__), "output_dir", val)
        # 存在check
        if os.path.exists(vtt_filepath):
            spinner.info("ローカルファイル「%s」は存在します。" % (val))
        else:
            spinner.fail("ローカルファイル「%s」は存在しません。" % (val))
            return False
    lang_cmd, map_cmd, input_file_cmd = generate_lang_cmd(vtt)
    if video.endswith(".mp4"):
        cmdline = (
            "ffmpeg -i "
            + video_filepath
            + input_file_cmd
            + " -map 0:v -map 0:a "
            + map_cmd
            + lang_cmd
            + " -c:v copy -c:a copy -c:s webvtt "
            + " {}-with_subtitles.mkv".format(video)
        )
        spinner.info("コマンド： 「{}」 を実行".format(cmdline))
        subprocess.call(cmdline, shell=True)
    spinner.stop()


def generate_lang_cmd(vtt):
    lang_format = {
        "ja": ("jpn", "Japanese"),  # 日本語
        "en": ("eng", "English"),  # 英語
        "es": ("spa", "Spanish"),  # スペイン語
        "zh": ("zho", "Chinese"),  # 中国語
        "ko": ("kor", "Korean"),  # 韓国語
        "pt": ("por", "Portuguese"),  # ポルトガル語
        "de": ("deu", "German"),  # ドイツ語
        "fr": ("fra", "French"),  # フランス語
    }
    lang_cmd = ""
    map_stream_cmd = ""
    input_file_cmd = ""
    for i, val in enumerate(vtt):
        lang_tuple = lang_format[val.split(".")[0]]
        lang_cmd += " -metadata:s:s:{} language={} -metadata:s:s:{} title='{}' ".format(
            i, lang_tuple[0], i, lang_tuple[1]
        )
        map_stream_cmd += " -map {} ".format(i + 1)
        input_file_cmd += " -i ./output_dir/{} ".format(val)
    return (lang_cmd, map_stream_cmd, input_file_cmd)


def main():
    merge_video_with_vvt(
        "Usage-of-S3-Buckets.mp4",  # 動画
        "en.Usage-of-S3-Buckets.vtt",  # 以下 vttファイル
        "es.en.Usage-of-S3-Buckets.vtt",
        "ko.en.Usage-of-S3-Buckets.vtt",
        "ja.en.Usage-of-S3-Buckets.vtt",
    )
    logger.info("ffmpeg job完了")


if __name__ == "__main__":
    main()
