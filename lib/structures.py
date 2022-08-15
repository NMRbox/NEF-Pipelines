from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass(frozen=True)
class SequenceResidue:
    chain: str
    sequence_code: int
    residue_name: str


# should contain a residue and have constructors?
@dataclass(frozen=True)
class AtomLabel:
    chain_code: str
    sequence_code: Optional[int]
    residue_name: str
    atom_name: str


@dataclass
class PeakAxis:
    atom_labels: List[AtomLabel]
    ppm: float
    # width: float
    # bound: float
    merit: str
    # j: float
    # U: str


@dataclass
class PeakValues:
    index: int
    volume: float
    intensity: float
    status: bool
    comment: str
    # flag0: str


@dataclass
class PeakListData:
    num_axis: int
    axis_labels: List[str]
    # isotopes: List[str]
    data_set: str
    sweep_widths: List[float]
    spectrometer_frequencies: List[float]


@dataclass
class PeakList:
    peak_list_data: PeakListData
    peaks: list[dict[Union[int, str], Union[PeakAxis, PeakValues]]]


@dataclass
class LineInfo:
    file_name: str
    line_no: int
    line: str


@dataclass
class ShiftData:
    atom: AtomLabel
    shift: float
    error: Optional[float] = None

@dataclass
class ShiftList:
    shifts: List[ShiftData]


@dataclass
class RdcRestraint:
    atom_1: AtomLabel
    atom_2: AtomLabel
    rdc: float
    rdc_error: float
    weight: Optional[float] = None