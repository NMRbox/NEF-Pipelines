import string
from enum import auto

from strenum import UppercaseStrEnum

# from https://www.kherb.io/docs/nmr_table.html
# The values are taken from the IAEA's table of recommended nuclear magnetic moments and have been converted to
# gyromagnetic ratios using the 2018 CODATA recommended values for the nuclear magneton and Planck's constant.
# However, the value for hydrogen has been replaced with the CODATA value. The number in parentheses represents
# the one-sigma (1σ) uncertainty in the last two digits of the value provided.
# this is agreement with the values in the Cavanagh et als book (2nd edition)
# 42.577478518 * 2 * 3.1415927 / 100 = 2.675221874410521 vs 2.6752 in Cavanagh within reasonable errors
# the value from NIST is 2.675 221 8708 (12) s-1 T-1 which is in agreement with the value in Cavanagh
MAGNETOGYRIC_RATIO_1H = 42.577478518  # uncertainty (18)  MHz/T


class Isotope(UppercaseStrEnum):
    H1 = auto()
    H2 = auto()
    H3 = auto()
    N15 = auto()
    C13 = auto()
    O17 = auto()
    F19 = auto()
    P31 = auto()

    def __str__(self):
        element = self.name.rstrip(string.digits)
        isotope_number = self.name[len(element) :]
        return f"{isotope_number}{element}"


# fmt: off
GAMMA_RATIOS = {
    # Nuc	        ratio	        # (MHz⋅T−1)
    Isotope.H1:     1.0,            # 42.58
    Isotope.H2:     0.153508386,    # 6.54
    Isotope.H3:     1.066643718,    # 45.42
    Isotope.C13:    0.251503855,    # 10.71
    Isotope.N15:    0.101368145,    # -4.32 - should really be negative !
    Isotope.O17:    0.135564627,    # -5.77 - should really be negative !
    Isotope.F19:    0.94129576,     # 40.08
    Isotope.P31:    0.404791467,    # 17.24
}

ATOM_TO_ISOTOPE = {
    # Nuc   Isotope
    "H": Isotope.H1,
    "D": Isotope.H2,
    "T": Isotope.H3,
    "C": Isotope.C13,
    "N": Isotope.N15,
    "O": Isotope.O17,
    "F": Isotope.F19,
    "P": Isotope.P31,
}
# fmt: on
