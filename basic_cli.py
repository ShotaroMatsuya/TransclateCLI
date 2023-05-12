import click
from click_help_colors import HelpColorsGroup
from ffmpeg_handler import merge_video_with_vvt
from halo import Halo
from pyfiglet import Figlet
from PyInquirer import Separator, Token, prompt, style_from_dict
from transcript_handler import amazon_transcribe
from translate_handler import amazon_translate
import os
import glob

style = style_from_dict(
    {
        Token.Separator: "#4169e1",
        Token.QuestionMark: "#673ab7 bold",
        Token.Selected: "#c71585",
        Token.Pointer: "#2e8b57 bold",
        Token.Instruction: "#f0e68c",
        Token.Answer: "#f44336 bold",
        Token.Question: "#808000",
    }
)

target_lang_list = [
    {"name": "ja"},
    {"name": "en"},
    {"name": "es"},
    {"name": "zh"},
    {"name": "ko"},
    {"name": "pt"},
    {"name": "de"},
    {"name": "fr"},
]

spinner = Halo(text="Loading", spinner="dots", color="magenta", text_color="cyan")


def get_output_dir_path():
    """Return the path of the output's directory.

    Returns:
        str: The output dir path.
    """
    output_dir = None
    # try:
    #     import settings
    #     if settings.TEMPLATE_PATH:
    #         output_dir = settings.TEMPLATE_PATH
    # except ImportError:
    #     pass

    if not output_dir:
        print(os.path.relpath(__file__))
        print(os.path.dirname(os.path.relpath(__file__)))
        base_dir = os.path.dirname(os.path.dirname(os.path.relpath(__file__)))
        print(base_dir)
        output_dir = os.path.join(base_dir, 'output_dir')

    return output_dir


def build_prompt_option(message, options):
    prompt_options_style = [
        {
            "type": "checkbox",
            "message": message,
            "name": "selected_lang",
            "choices": [],
            "validate": lambda lang: "You must choose at least one language"
            if len(lang) == 0
            else True,
        }
    ]
    prompt_options_style[0]["choices"].append(Separator("= Choose target languages ="))
    for opt in options:
        prompt_options_style[0]["choices"].append(opt)
    prompt_options_style[0]["choices"].append(Separator("======================"))
    return prompt_options_style


def build_prompt_option_files(message, option_type, options: list):
    prompt_options_style = [
        {
            "type": option_type,  # "list" , "checkbox"
            "message": message,
            "name": "selected_file",
            "choices": options,
            "validate": lambda file: "You must choose at least one file"
            if len(file) == 0
            else True,
        }
    ]
    return prompt_options_style


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="cyan"
)
@click.version_option("0.0.1", prog_name="transcrate")
def main():
    """Transcrate CLI"""
    pass


@main.command("start-all")
@click.argument("media_file", required=True)
@click.option(
    "--native",
    "-n",
    default="ja",
    help="Option to select the speaker's native language (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)",
    type=click.Choice(["ja", "en", "ko", "zh", "es", "pt", "de", "fr"]),
)
def entire_jobs_start(media_file, native):
    """Create Transcription in various languages
    and Embed it as Subtitles in Movies
    (powered by AWS AI services)
    """
    try:
        amazon_transcribe(media_file, native)
        click.echo(
            "successfully create transcript for {} in lang ({})".format(
                media_file, native
            )
        )
    except (KeyboardInterrupt, SystemExit):
        spinner.fail("Error occurred!")

    click.secho(
        "You can improve your transcription output manually if necessary",
        fg="blue",
        bg="yellow",
    )
    if click.confirm("Are you sure to continue the translation job?"):
        user_inputs = prompt(
            build_prompt_option(
                "Select the languages (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)",
                target_lang_list,
            ),
            style=style,
        )
        click.echo(user_inputs["selected_lang"])

        try:
            amazon_translate(
                "{}.{}.vtt".format(native, media_file.split(".")[0]),
                *user_inputs["selected_lang"]
            )
            click.echo(
                "successfully Finished translate job for {} in lang::{}".format(
                    media_file, *user_inputs["selected_lang"]
                )
            )
        except (KeyboardInterrupt, SystemExit):
            spinner.fail("Error occurred!")

    if click.confirm("Are you sure to continue to embed subtitles in your videos?"):
        source_vtt = "{}.{}.vtt".format(native, media_file.split(".")[0])
        target_vtt_list = list(
            map(
                lambda lang: "{}.{}".format(lang, source_vtt),
                user_inputs["selected_lang"],
            )
        )
        try:
            merge_video_with_vvt(media_file, source_vtt, *target_vtt_list)
            click.echo("successfully embed subtitles in your videos.")
        except (KeyboardInterrupt, SystemExit):
            spinner.fail("Error occurred!")


@main.command("start-transcribe")
@click.argument("media_file", required=True)
@click.option(
    "--native",
    "-n",
    default="ja",
    help="select the speaker's native (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)",
    type=click.Choice(["ja", "en", "ko", "zh", "es", "pt", "de", "fr"])
)
def transcribe_job(media_file, native):
    try:
        amazon_transcribe(media_file, native)
        click.echo(
            "successfully create transcript for {} in lang ({})".format(
                media_file, native
            )
        )
    except (KeyboardInterrupt, SystemExit):
        spinner.fail("Error occurred!")


@main.command("start-translate")
@click.argument("vtt_file", required=False)
def translate_job(vtt_file):
    dir_path = get_output_dir_path()
    if vtt_file is not None and os.path.exists(os.path.join(dir_path, vtt_file)):
        user_inputs = prompt(
            build_prompt_option(
                "Select the target languages (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)",
                target_lang_list,
            ),
            style=style,
        )
        click.echo(user_inputs["selected_lang"])            
    else:
        target_path = "{dir_path}/*.vtt".format(dir_path=dir_path)
        # vttの拡張子のファイルリスト取得
        vtt_file_list = map(lambda x: {"name": x}, glob.glob(target_path))
        print(vtt_file_list)
        vtt_file = prompt(
            build_prompt_option_files(
                "Select the input vtt file",
                "list",
                vtt_file_list
            )
        )
        click.echo(vtt_file["selected_file"])
        user_inputs = prompt(
            build_prompt_option(
                "Select the target languages (ja: 日本語, en: 英語, ko: 韓国語, zh: 中国語, es: スペイン語, pt: ポルトガル語, de:ドイツ語, fr: フランス語)",
                target_lang_list,
            ),
            style=style,
        )
        click.echo(user_inputs["selected_lang"])   
    try:
        amazon_translate(
            vtt_file["selected_file"].split("/")[1],
            *user_inputs["selected_lang"]
        )
        click.echo(
            "successfully Finished translate job in lang::{}".format(
                *user_inputs["selected_lang"]
            )
        )
    except (KeyboardInterrupt, SystemExit):
        spinner.fail("Error occurred!")
    
    
@main.command("start-embed")
@click.argument("media_file", required=True)
def embed_caption_in_video(media_file):
    dir_path = get_output_dir_path()
    target_path = "{dir_path}/*.vtt".format(dir_path=dir_path)
    # vttの拡張子のファイルリスト取得
    vtt_file_list = map(lambda x: {"name": x}, glob.glob(target_path))
    print(vtt_file_list)
    vtt_file = prompt(
        build_prompt_option_files(
            "Select the input vtt file",
            "checkbox",
            vtt_file_list
        )
    )
    vtt_file_list = map(lambda x: x.split("/")[1], vtt_file["selected_file"])
    print(vtt_file["selected_file"])
    merge_video_with_vvt(media_file, *vtt_file_list)
    

@main.command()
def info():
    """Info About CLI"""
    click.echo(
        "Create Transcription in various languages and Embed it as Subtitles in Movies (powered by AWS AI services)"
    )
    f = Figlet(font="slant")
    click.echo(f.renderText("Transclate CLI"))
    click.secho("Author: shotaro matsuya", fg="cyan")
