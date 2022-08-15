from typing import List, Tuple, Dict

import tabulate
from transcoders.pales import export_app
import typer

from lib.sequence_lib import get_sequence_or_exit

from lib.sequence_lib import sequence_residues_to_sequence_3let, translate_3_to_1
from lib.util import chunks, exit_error, read_float_or_exit

from lib.structures import SequenceResidue, RdcRestraint, AtomLabel


app = typer.Typer()

# noinspection PyUnusedLocal
@export_app.command()
def template(
    chain_code: str = typer.Option('A', '-c', '--chain', help='chain code a single chain code',
                                   metavar='<CHAIN-CODE>'),
    template_atoms: Tuple[str, str] = typer.Option(('HN', 'N'), '-a', '--atoms', help='for templates the atoms for the restraintsb to be between'),
    # see _parse_weights for parsing and adding defaults
    raw_weights: List[str] = typer.Option([], '-w', '--weight', help='weights for rdcs as a comma separated triple of 2 atom names and a weight [no spaces e.g HN,N,1.0], multiple weights may be added by repeated calls, efault is HN,N,1.0'),
):
    """convert nef rdc restraints to pales template file for prediction of rdcs"""

    weights = _parse_weights(raw_weights)
    sequence = get_sequence_or_exit()

    sequence_3_let = sequence_residues_to_sequence_3let(sequence)

    sequence_1_let = translate_3_to_1(sequence_3_let)

    print(f'REMARK NEF CHAIN {chain_code}')
    print(f'REMARK NEF START RESIDUE {sequence[0].sequence_code}')
    print()
    _print_pipe_sequence(sequence_1_let)

    restaints = _build_dummy_restraints(sequence, template_atoms) if template else _read_rdcs_from_nef()

    print()
    _print_restraints(restaints, weights=weights)

def _parse_weights(raw_weights):

    result  = {}
    for raw_weight in raw_weights:

        raw_weight_fields = raw_weight.split(',')

        if len(raw_weight_fields) != 3:
            exit_error(f'bad weight {raw_weight} weights should have 3 fields separated by commas [no spaces] atom_1,atom_2,weight. e.g HN,N,1.0')

        atom_1, atom_2, raw_rdc_weight =  raw_weight_fields

        rdc_weight = read_float_or_exit(raw_rdc_weight, message=f'weights should have 3 fields separated by commas [no spaces] atom_1,atom_2,weight weight should be a float i got {raw_weight} for field feild [{raw_rdc_weight}] which is not a float')

        key = _build_weights_key(atom_1, atom_2)
        result[key] = rdc_weight

    # it not possibe to add default weights?
    HN_N_key = _build_weights_key('HN', 'N')
    if not HN_N_key in result:
        result[HN_N_key] = 1.0

    return result

def _build_weights_key(atom_1, atom_2):
    return tuple(sorted([atom_1, atom_2]))

def _build_dummy_restraints(sequence: SequenceResidue, atom_names: Tuple[str, str]) -> List[RdcRestraint]:
    """
    note we use xplor names as pales is a NIH product
    :param sequence:
    :param atom_names:
    :return:
    """
    restraints = []
    for residue in sequence:

        # special case prolines, but really we should check chem comap for atoms...
        if residue.residue_name == 'PRO' and 'HN' in atom_names:
            continue
        atom_1 =  AtomLabel(residue.chain, residue.sequence_code, residue.residue_name, atom_names[0])
        atom_2 = AtomLabel(residue.chain, residue.sequence_code, residue.residue_name, atom_names[1])
        restraint = RdcRestraint(atom_1, atom_2, 0.0, 0.0)
        restraints.append(restraint)

    return restraints

def _print_restraints(restraints: List[RdcRestraint], weights: Dict[Tuple[str, str], float]):
    VARS = 'VARS   RESID_I RESNAME_I ATOMNAME_I RESID_J RESNAME_J ATOMNAME_J D DD W'.split()
    FORMAT = 'FORMAT %5d     %6s       %6s        %5d     %6s    %6s %9.3f %9.3f %.2f'.split()

    table = [VARS, FORMAT]

    for i, restraint in enumerate(restraints):
        atom_1 = restraint.atom_1
        atom_2 = restraint.atom_2

        weights_key = _build_weights_key(atom_1.atom_name, atom_2.atom_name)
        weight = weights[weights_key]
        row = ['', atom_1.sequence_code, atom_1.residue_name, atom_1.atom_name,
               atom_2.sequence_code, atom_2.residue_name, atom_2.atom_name, 0.000, 0.000, weight]
        table.append(row)

    print(tabulate.tabulate(table, tablefmt='plain'))


def _print_pipe_sequence(sequence_1_let: List[str]):

    rows = chunks(sequence_1_let, 100)

    for row in rows:
        row_chunks = list(chunks(row, 10))
        row_strings = [''.join(chunk) for chunk in row_chunks]
        print(f'DATA SEQUENCE {" ".join(row_strings)}')


