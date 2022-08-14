import sys
from fnmatch import fnmatch
from typing import List

from ordered_set import OrderedSet
from typer import Option, Argument

from lib.util import get_pipe_file, chunks
from tools.chains import chains_app
import typer

from pynmrstar import Entry

app = typer.Typer()

#TODO: it would be nice to put the chains with the first molecular system frame

# noinspection PyUnusedLocal
@chains_app.command()
def rename(
    old: str = Argument(...,  help='old chain code'),
    new: str = Argument(..., help='new chain code'),
    comment: bool = Option(False, '-c', '--comment', help='prepend comment to chains'),
    verbose: bool = Option(False, '-v', '--verbose', help='print verbose info'),
    frames: List[str] = Option([], '-f', '--frame', help='limit changes to a a particular frame'),

):
    """- change the name of a chain"""

    lines = ''.join(get_pipe_file([]).readlines())
    entry = Entry.from_string(lines)

    changes = 0
    changed_frames = OrderedSet()
    for save_frame in entry:
        if len(frames) >= 1:
            for frame_selector in frames:
                if not fnmatch(save_frame.name, f'*{frame_selector}*'):
                    continue
        for loop in save_frame.loop_iterator():
            for tag in loop.get_tag_names():
                tag_parts = tag.split('.')
                if tag_parts[-1].startswith('chain_code'):
                    tag_values = loop[tag]
                    for i, row in enumerate(tag_values):
                        if row == old:
                            tag_values[i] = new
                            changes += 1
                            changed_frames.add(save_frame.name)

                    loop[tag] = tag_values

    if verbose:
        comment = '# ' if comment else ''
        out = sys.stderr if not comment else sys.stdout
        if changes >= 1:
            print(f'{comment}rename chain: {changes} changes made in the following frames', file=out)
            for chunk in chunks(changed_frames, 5):
                print(f'{comment}  {", ".join(chunk)}', file=out)

        else:
            print(f'{comment}rename chain: no changes made', file=out)
        print(file=out)

    print(entry)


