from itertools import chain, cycle, islice, zip_longest
from pathlib import Path
from typing import Iterable, List

import typer
from Bio.SeqIO.FastaIO import SimpleFastaParser
from ordered_set import OrderedSet

from nef.lib.sequence_lib import (
    chain_code_iter,
    offset_chain_residues,
    sequence_3let_to_res,
    sequence_to_nef_frame,
    translate_1_to_3,
)
from nef.lib.structures import SequenceResidue
from nef.lib.typer_utils import get_args
from nef.lib.util import (
    exit_error,
    parse_comma_separated_options,
    process_stream_and_add_frames,
)
from nef.transcoders.fasta import import_app

app = typer.Typer()

NO_CHAIN_START_HELP = """don't include the start chain link type on a chain for the first residue [linkage will be
                         middle] for the named chains. Either use a comma joined list of chains [e.g. A,B] or call this
                         option multiple times to set chain starts for multiple chains"""
NO_CHAIN_END_HELP = """don't include the end chain link type on a chain for the last residue [linkage will be
                       middle] for the named chains. Either use a comma joined list of chains [e.g. A,B] or call this
                       option multiple times to set chain ends for multiple chains"""


# todo add comment to other sequences etc
@import_app.command()
def sequence(
    chain_codes: List[str] = typer.Option(
        [],
        "--chains",
        help="chain codes to use for the exported chains, can be a a comma sepatared list or can be called "
        "multiple times",
        metavar="<CHAIN-CODES>",
    ),
    starts: List[str] = typer.Option(
        [],
        "--starts",
        help="first residue number of sequences can be a comma separated list or ",
        metavar="<START>",
    ),
    no_chain_starts: List[str] = typer.Option(
        [], "--no-chain-start", help=NO_CHAIN_START_HELP
    ),
    no_chain_ends: List[str] = typer.Option(
        [], "--no-chain-end", help=NO_CHAIN_END_HELP
    ),
    entry_name: str = typer.Option("fasta", help="a name for the entry if required"),
    pipe: List[Path] = typer.Option(
        None,
        metavar="|PIPE|",
        help="pipe to read NEF data from, for testing [overrides stdin !use stdin instead!]",
    ),
    file_names: List[Path] = typer.Argument(
        ..., help="the file to read", metavar="<FASTA-FILE>"
    ),
):
    """- convert fasta sequence to nef"""

    chain_codes = parse_comma_separated_options(chain_codes)
    no_chain_starts = parse_comma_separated_options(no_chain_starts)
    no_chain_ends = parse_comma_separated_options(no_chain_ends)
    starts = [int(elem) for elem in parse_comma_separated_options(starts)]

    args = get_args()

    process_sequences(args)


def process_sequences(args):
    fasta_frames = []

    chain_code_iterator = chain_code_iter(args.chain_codes)
    fasta_sequences = OrderedSet()
    for file_path in args.file_names:
        fasta_sequences.update(read_sequences(file_path, chain_code_iterator))

    read_chain_codes = residues_to_chain_codes(fasta_sequences)

    offsets = _get_sequence_offsets(read_chain_codes, args.starts)

    fasta_sequences = offset_chain_residues(fasta_sequences, offsets)

    fasta_sequences = sorted(
        fasta_sequences, key=lambda x: (x.chain_code, x.sequence_code)
    )

    fasta_frames.append(sequence_to_nef_frame(fasta_sequences))

    entry = process_stream_and_add_frames(fasta_frames, args)

    print(entry)


def _get_sequence_offsets(chain_codes: List[str], starts: List[int]):

    offsets = [start - 1 for start in starts]
    cycle_starts = chain(
        offsets,
        cycle(
            [
                0,
            ]
        ),
    )
    offsets = list(islice(cycle_starts, len(chain_codes)))

    return {chain_code: offset for chain_code, offset in zip(chain_codes, offsets)}


def residues_to_chain_codes(residues: List[SequenceResidue]) -> List[str]:
    return list(OrderedSet([residue.chain_code for residue in residues]))


# could do with taking a list of offsets
# noinspection PyUnusedLocal
def read_sequences(path: Path, chain_codes: Iterable[str]) -> List[SequenceResidue]:

    residues = OrderedSet()
    try:
        with open(path) as handle:
            try:
                sequences = list(SimpleFastaParser(handle))
            except Exception as e:
                # check if relative to os.getcwd
                exit_error(f"Error reading fasta file {str(path)}", e)

            number_sequences = len(sequences)

            # read as many chain codes as there are sequences
            # https://stackoverflow.com/questions/16188270/get-a-fixed-number-of-items-from-a-generator

            chain_codes = list(islice(chain_codes, number_sequences))

            for (meta_data, sequence), chain_code in zip_longest(
                sequences, chain_codes
            ):

                sequence_3_let = translate_1_to_3(sequence)
                chain_residues = sequence_3let_to_res(sequence_3_let, chain_code)

                residues.update(chain_residues)

    except IOError as e:
        exit_error(f"couldn't open {path} because:\n{e}", e)

    return residues
