from ogphl import macro_params, income
from ogphl import input_output as io
import os
import warnings
import numpy as np
import datetime

UN_COUNTRY_CODE = "608"


class Calibration:
    """OG-PHL calibration class"""

    def __init__(
        self,
        p,
        macro_data_start_year=datetime.datetime(1947, 1, 1),
        macro_data_end_year=datetime.datetime(2023, 1, 1),
        demographic_data_path=None,
        output_path=None,
        update_from_api=False,
    ):
        """
        Constructor for the Calibration class.

        Args:
            p (OG-Core Specifications object): model parameters
            macro_data_start_year (datetime): start date for macro data
            macro_data_end_year (datetime): end date for macro data
            demographic_data_path (str): path to save demographic data
            output_path (str): path to save output to
            update_from_api (bool): Set True to pull updated data from
                online sources

        Returns:
            None

        """
        # Create output_path if it doesn't exist
        if output_path is not None:
            if not os.path.exists(output_path):
                os.makedirs(output_path)

        # Initialize with overlay values only. Existing values on p are the
        # baseline from the packaged defaults.
        self.macro_params = {}
        self.demographic_params = {}
        self.e = None
        self.alpha_c = np.array([1.0]) if p.I == 1 else None
        self.io_matrix = np.array([[1.0]]) if p.M == 1 else None
        # gamma (capital share by industry) is only overlaid for the
        # multi-industry model; for M == 1 the packaged baseline value is kept.
        self.gamma = None

        if not update_from_api:
            return

        # Macro estimation
        try:
            self.macro_params = macro_params.get_macro_params(
                macro_data_start_year,
                macro_data_end_year,
                update_from_api=update_from_api,
            )
        except Exception as exc:
            warnings.warn(f"Macro params update failed: {exc}", stacklevel=2)

        # io matrix and alpha_c
        if p.I > 1:
            try:
                alpha_c_dict = io.get_alpha_c()
                # check that model dimensions are consistent with alpha_c
                assert p.I == len(list(alpha_c_dict.keys()))
                self.alpha_c = np.array(list(alpha_c_dict.values()))
            except Exception as exc:
                warnings.warn(f"alpha_c update failed: {exc}", stacklevel=2)
        if p.M > 1:
            try:
                # value-added content of consumption by industry (see
                # input_output.get_io_matrix_value_added); the legacy
                # get_io_matrix is retained only as a comparison baseline
                io_df = io.get_io_matrix_value_added()
                # check that model dimensions are consistent with io_matrix
                assert p.M == len(list(io_df.keys()))
                self.io_matrix = io_df.values
            except Exception as exc:
                warnings.warn(f"io_matrix update failed: {exc}", stacklevel=2)
            try:
                gamma_dict = io.get_gamma()
                # check that model dimensions are consistent with gamma
                assert p.M == len(list(gamma_dict.keys()))
                self.gamma = np.array(list(gamma_dict.values()))
            except Exception as exc:
                warnings.warn(f"gamma update failed: {exc}", stacklevel=2)

        # Demographics and income are atomic because e depends on demography.
        try:
            from ogcore import demographics

            self.demographic_params = demographics.get_pop_objs(
                p.E,
                p.S,
                p.T,
                0,
                99,
                country_id=UN_COUNTRY_CODE,
                initial_data_year=p.start_year - 1,
                final_data_year=p.start_year + 1,
                GraphDiag=False,
                download_path=demographic_data_path,
            )

            # demographics for 80 period lives (needed for getting e below)
            demog80 = demographics.get_pop_objs(
                20,
                80,
                p.T,
                0,
                99,
                country_id=UN_COUNTRY_CODE,
                initial_data_year=p.start_year - 1,
                final_data_year=p.start_year + 1,
                GraphDiag=False,
            )

            # earnings profiles
            self.e = income.get_e_interp(
                p.E,
                p.S,
                p.J,
                p.lambdas,
                demog80["omega_SS"],
            )
        except Exception as exc:
            warnings.warn(
                f"Demographics/income update failed: {exc}", stacklevel=2
            )
            self.demographic_params = {}
            self.e = None

    # method to return all newly calibrated parameters in a dictionary
    def get_dict(self):
        d = {}
        d.update(self.macro_params)
        d.update(self.demographic_params)
        if self.e is not None:
            d["e"] = self.e
        if self.alpha_c is not None:
            d["alpha_c"] = self.alpha_c
        if self.io_matrix is not None:
            d["io_matrix"] = self.io_matrix
        if self.gamma is not None:
            d["gamma"] = self.gamma

        return d
