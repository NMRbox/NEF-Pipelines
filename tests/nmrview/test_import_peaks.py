import pytest

import lib
from lib.test_lib import (
    assert_lines_match,
    isolate_frame,
    path_in_test_data,
    run_and_report,
)

MOLECULAR_SYSTEM_NMRVIEW = "nef_spectrum_nmrview"
NMRVIEW_IMPORT_PEAKS = ["nmrview", "import", "peaks"]


@pytest.fixture
def using_nmrview():
    # register the module under test
    import transcoders.nmrview  # noqa: F401


EXPECTED_4AA = open(
    path_in_test_data(__file__, "nmrview_expected_4aa.txt", local=True)
).read()


# noinspection PyUnusedLocal
def test_3peaks(typer_app, using_nmrview, clear_cache, monkeypatch):

    # reading stdin doesn't work in pytest so for a clean header
    # TODO move to conftest.py
    monkeypatch.setattr(lib.util, "get_pipe_file", lambda x: None)
    peaks_path = path_in_test_data(__file__, "4peaks.xpk", local=True)
    sequence_path = path_in_test_data(__file__, "4peaks.seq")

    args = [
        *NMRVIEW_IMPORT_PEAKS,
        "--sequence",
        sequence_path,
        "--axis",
        "1H.1H.15N",
        peaks_path,
    ]
    result = run_and_report(typer_app, args)

    result = isolate_frame(result.stdout, "nef_nmr_spectrum_simnoe")

    assert_lines_match(EXPECTED_4AA, result)


def test_3peaks_bad_axis_codes(typer_app, using_nmrview, clear_cache, monkeypatch):

    # reading stdin doesn't work in pytest so for a clean header
    # TODO move to conftest.py
    monkeypatch.setattr(lib.util, "get_pipe_file", lambda x: None)
    peaks_path = path_in_test_data(__file__, "4peaks.xpk")
    sequence_path = path_in_test_data(__file__, "4peaks.seq")
    args = [
        *NMRVIEW_IMPORT_PEAKS,
        "--sequence",
        sequence_path,
        "--axis",
        "1H,15N",
        peaks_path,
    ]
    result = run_and_report(typer_app, args, expected_exit_code=1)

    EXPECTED = """\
    ERROR: can't find isotope code for axis 2 got axis codes 1H,15N
    exiting..."""

    assert_lines_match(EXPECTED, result.stdout)


EXPECTED_JOE_CLIC = """\
    save_nef_nmr_spectrum_trosyrdcjoe
       _nef_nmr_spectrum.sf_category          nef_nmr_spectrum
       _nef_nmr_spectrum.sf_framecode         nef_nmr_spectrum_trosyrdcjoe
       _nef_nmr_spectrum.num_dimensions       2
       _nef_nmr_spectrum.chemical_shift_list  .

       loop_
          _nef_spectrum_dimension.dimension_id
          _nef_spectrum_dimension.axis_unit
          _nef_spectrum_dimension.axis_code
          _nef_spectrum_dimension.spectrometer_frequency
          _nef_spectrum_dimension.spectral_width
          _nef_spectrum_dimension.value_first_point
          _nef_spectrum_dimension.folding
          _nef_spectrum_dimension.absolute_peak_positions
          _nef_spectrum_dimension.is_acquisition



           1   ppm   1H   600.052978516    6.1679  .   circular   true   .
           2   ppm   1H   60.8100013733   35.9997  .   circular   true   .


       stop_

       loop_
          _nef_spectrum_dimension_transfer.dimension_1
          _nef_spectrum_dimension_transfer.dimension_2
          _nef_spectrum_dimension_transfer.transfer_type


       stop_

       loop_
          _nef_peak.index
          _nef_peak.peak_id
          _nef_peak.volume
          _nef_peak.volume_uncertainty
          _nef_peak.height
          _nef_peak.height_uncertainty
          _nef_peak.position_1
          _nef_peak.position_uncertainty_1
          _nef_peak.position_2
          _nef_peak.position_uncertainty_2
          _nef_peak.chain_code_1
          _nef_peak.sequence_code_1
          _nef_peak.residue_name_1
          _nef_peak.atom_name_1
          _nef_peak.chain_code_2
          _nef_peak.sequence_code_2
          _nef_peak.residue_name_2
          _nef_peak.atom_name_2

          1   0   0.254054695368   .   0.0368   .   8.15968   .   126.97411   .   A   2   ala   H   A   2   ala   N

       stop_

    save_
"""


# noinspection PyUnusedLocal
def test_joe_bad_sweep_widths(typer_app, using_nmrview, monkeypatch):

    # reading stdin doesn't work in pytest so for a clean header
    # TODO move to conftest.py
    monkeypatch.setattr(lib.util, "get_pipe_file", lambda x: None)
    peaks_path = path_in_test_data(__file__, "joe_clic.xpk")
    sequence_path = path_in_test_data(__file__, "4peaks.seq")

    command = [
        *NMRVIEW_IMPORT_PEAKS,
        "--sequence",
        sequence_path,
        "--axis",
        "1H.1H.15N",
        peaks_path,
    ]
    result = run_and_report(typer_app, command)

    result = isolate_frame(result.stdout, "nef_nmr_spectrum_trosyrdcjoe")

    assert_lines_match(EXPECTED_JOE_CLIC, result)


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
