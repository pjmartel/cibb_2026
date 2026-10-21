import importlib.util
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_helper(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "pymol_scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lig = load_helper("ligand_align")
analysis = load_helper("alignment_analysis")


class MathTests(unittest.TestCase):
    def test_rigid_transform(self):
        x = np.array([[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3.]])
        rotation = np.array([[0, -1., 0], [1., 0, 0], [0, 0, 1.]])
        y = x @ rotation + np.array([7, -3, 9])
        r, t, rmsd = lig.rigid_fit(x, y)
        np.testing.assert_allclose(x @ r + t, y, atol=1e-10)
        self.assertLess(rmsd, 1e-10)
        self.assertAlmostEqual(np.linalg.det(r), 1)

    def test_reflection_is_not_permitted(self):
        x = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])
        y = x * [-1, 1, 1]
        r, _, rmsd = lig.rigid_fit(x, y)
        self.assertAlmostEqual(np.linalg.det(r), 1)
        self.assertGreater(rmsd, 0.1)

    def test_collinear_and_short_maps_rejected(self):
        for points in ([[0, 0, 0], [1, 0, 0]], [[0, 0, 0], [1, 0, 0], [2, 0, 0]]):
            with self.assertRaises(ValueError):
                lig.rigid_fit(points, points)

    def test_column_metrics(self):
        result = analysis.column_metrics([[0, 0, 0], [2, 0, 0]], ["ALA", "GLY"])
        self.assertAlmostEqual(result["ca_rms_dispersion_A"], 1)
        self.assertAlmostEqual(result["consensus_fraction"], 0.5)


@unittest.skipUnless(importlib.util.find_spec("pymol2"), "Optional PyMOL integration dependency is absent.")
class PyMOLTests(unittest.TestCase):
    def setUp(self):
        import pymol2
        self.pm = pymol2.PyMOL()
        self.pm.start()
        self.cmd = self.pm.cmd
        lig.cmd = self.cmd
        analysis.cmd = self.cmd
        self.cmd.load(str(ROOT / "pymol_scripts/examples/lysozyme_benzene.pdb"), "reference")
        self.cmd.create("mobile1", "reference")
        self.cmd.rotate("y", 32, "mobile1")
        self.cmd.translate([9, 3, -4], "mobile1")

    def tearDown(self):
        self.pm.stop()

    def test_ligand_fit_preserves_input(self):
        before = self.cmd.get_coords("mobile1").copy()
        result = lig.ligand_align("mobile1 and resn BNZ", "reference and resn BNZ")
        self.assertLess(result["mapped_atom_rmsd_A"], 1e-4)
        np.testing.assert_allclose(self.cmd.get_coords("mobile1"), before)
        np.testing.assert_allclose(self.cmd.get_coords("ligand_fitted"), self.cmd.get_coords("reference"), atol=1e-3)
        with self.assertRaises(ValueError):
            lig.ligand_align("mobile1 and resn BNZ", "reference and resn BNZ")

    def test_three_model_report_and_lf(self):
        self.cmd.create("mobile2", "reference")
        self.cmd.rotate("x", -27, "mobile2")
        self.cmd.translate([-7, -4, 6], "mobile2")
        analysis.class_multi_align("reference", "mobile1 mobile2")
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory) / "alignment")
            result = analysis.alignment_report(prefix=prefix, reference="reference")
            self.assertEqual(len(result["objects"]), 3)
            self.assertEqual(result["CA_columns"], self.cmd.count_atoms("reference and polymer.protein and name CA and (alt ''+A)"))
            self.assertTrue(all(p["common_CA_columns"] == result["CA_columns"] for p in result["pairwise"]))
            self.assertTrue(all(p["current_frame_CA_rmsd_A"] < 1e-3 for p in result["pairwise"]))
            for p in Path(directory).iterdir():
                self.assertNotIn(b"\r", p.read_bytes())

    def test_real_pymol_command_line_demo(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            shutil.copytree(ROOT / "pymol_scripts", folder / "pymol_scripts")
            script = (
                "@pymol_scripts/examples/demo_helpers.pml\n"
                "ligand_align mobile1 and resn BNZ, reference and resn BNZ, , empty_map_fit, ligand\n"
                "ligand_align mobile1 and resn BNZ, reference and resn BNZ, C1:C1|C2:C2|C3:C3, mapped_ligand, ligand\n"
            )
            (folder / "test.pml").write_text(script, encoding="utf-8", newline="\n")
            result = subprocess.run([sys.executable, "-m", "pymol", "-cq", "test.pml"], cwd=folder,
                                    capture_output=True, text=True, timeout=30)
            log = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, log)
            self.assertNotIn("Traceback", log)
            self.assertIn("ligand_fitted: 6 mapped heavy atoms", log)
            self.assertIn("empty_map_fit: 6 mapped heavy atoms", log)
            self.assertIn("mapped_ligand: 3 mapped heavy atoms", log)
            self.assertTrue((folder / "analysis-results/demo.summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
