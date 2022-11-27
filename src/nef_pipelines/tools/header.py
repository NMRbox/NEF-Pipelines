import typer
from pynmrstar import Entry

from nef_pipelines import nef_app
from nef_pipelines.lib.constants import NEF_PIPELINES, NEF_PIPELINES_VERSION
from nef_pipelines.lib.header_lib import create_header_frame
from nef_pipelines.lib.typer_utils import get_args


# noinspection PyUnusedLocal
@nef_app.app.command()
def header(
    name: str = typer.Argument("nef", help="name for the entry", metavar="<ENTRY-NAME>")
):
    """-  add a header to the stream"""
    args = get_args()

    entry = build_meta_data(args)

    print(entry)


def build_meta_data(args):
    from lib.util import script_name

    result = Entry.from_scratch(args.name)
    header_frame = create_header_frame(
        NEF_PIPELINES, NEF_PIPELINES_VERSION, script_name(__file__)
    )
    result.add_saveframe(header_frame)

    return result


if __name__ == "__main__":
    typer.run(header)
