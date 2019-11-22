import os
import subprocess
import tempfile
import nbformat


class TestExamples:

    def _notebook_run(self, path):
        """
        Execute a notebook via nbconvert and collect output.
        Returns (parsed nb object, execution errors)
        """
        dirname, __ = os.path.split(path)
        os.chdir(dirname)
        with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
            args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                    "--ExecutePreprocessor.timeout=200",
                    "--output", fout.name, path]
            subprocess.check_call(args)

            fout.seek(0)
            nb = nbformat.read(fout, nbformat.current_nbformat)

        errors = [output for cell in nb.cells if "outputs" in cell
                  for output in cell["outputs"]
                  if output.output_type == "error"]

        return nb, errors

    def test_load_era5_ipynb(self):
        parent_dirname = os.path.dirname(os.path.dirname(__file__))
        nb, errors = self._notebook_run(
            os.path.join(parent_dirname, 'example',
                         'load_era5_weather_data.ipynb'))
        assert errors == []

    def test_pvlib_ipynb(self):
        parent_dirname = os.path.dirname(os.path.dirname(__file__))
        nb, errors = self._notebook_run(
            os.path.join(parent_dirname, 'example',
                         'run_pvlib_model.ipynb'))
        assert errors == []

    def test_windpowerlib_turbine_ipynb(self):
        parent_dirname = os.path.dirname(os.path.dirname(__file__))
        nb, errors = self._notebook_run(
            os.path.join(parent_dirname, 'example',
                         'run_windpowerlib_turbine_model.ipynb'))
        assert errors == []
