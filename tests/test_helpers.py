"""Tests around the owner's unchanged scripts; PyMOL tests are optional in CI."""
import ast
import contextlib
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "pymol_scripts"


def pure_ligand_functions():
    """Exercise the actual pure functions without needing to import PyMOL."""
    tree = ast.parse((SCRIPTS / "ligalign.py").read_text())
    names = {"_kabsch", "_rmsd", "_boolarg", "_refined_labels",
             "_isomorphisms", "_score", "_best"}
    namespace = {"np": np}
    module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)
                             and n.name in names], type_ignores=[])
    exec(compile(module, "ligalign.py", "exec"), namespace)
    return SimpleNamespace(**namespace)


def load_script(name):
    spec = importlib.util.spec_from_file_location("author_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SourceTests(unittest.TestCase):
    def test_author_sources_preserved(self):
        manifest = json.loads((SCRIPTS / "source-manifest.json").read_text())
        for filename, entry in manifest["files"].items():
            self.assertEqual(sha256((SCRIPTS / filename).read_bytes()).hexdigest(), entry["sha256"])


class MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = pure_ligand_functions()

    def test_kabsch_rigid_transform(self):
        x = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])
        r0 = np.array([[0., -1, 0], [1, 0, 0], [0, 0, 1]])
        y = x @ r0.T + [7, -3, 9]
        rmsd, r, t = self.fn._kabsch(x, y)
        self.assertLess(rmsd, 1e-10)
        np.testing.assert_allclose(x @ r.T + t, y, atol=1e-10)
        self.assertAlmostEqual(np.linalg.det(r), 1)

    def test_reflection_not_used_as_rotation(self):
        x = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])
        rmsd, r, _ = self.fn._kabsch(x, x * [-1, 1, 1])
        self.assertAlmostEqual(np.linalg.det(r), 1)
        self.assertGreater(rmsd, .1)

    def test_benzene_symmetry_and_permuted_atom_order(self):
        a = np.arange(6) * np.pi / 3
        xyz = np.column_stack([np.cos(a), np.sin(a), np.zeros(6)])
        edges = {i: {(i - 1) % 6: 1, (i + 1) % 6: 1} for i in range(6)}
        target = SimpleNamespace(n=6, nbonds=6, elem=["C"]*6, hyd=[[] for _ in a],
                                 adj=list(edges.values()), xyz=xyz)
        order = [2, 0, 5, 3, 1, 4]
        inverse = {old: new for new, old in enumerate(order)}
        mobile = SimpleNamespace(n=6, nbonds=6, elem=["C"]*6, hyd=[[] for _ in a],
                                  adj=[{inverse[j]: o for j, o in edges[i].items()} for i in order],
                                  xyz=xyz[order])
        mappings = list(self.fn._isomorphisms(target, mobile, False, 20000))
        self.assertEqual(len(mappings), 12)
        candidates, count = self.fn._best(mappings, target, mobile, False)
        self.assertEqual(count, 12)
        self.assertAlmostEqual(self.fn._score(candidates[0], target, mobile, False), 0)
        self.assertGreater(self.fn._rmsd(mobile.xyz, target.xyz), .5)

    def test_inplace_and_fitted_are_different_metrics(self):
        x = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
        self.assertAlmostEqual(self.fn._rmsd(x + [0, 0, 2], x), 2)
        self.assertLess(self.fn._kabsch(x + [0, 0, 2], x)[0], 1e-10)


@unittest.skipUnless(importlib.util.find_spec("pymol2"), "Optional PyMOL integration dependency is absent.")
class PyMOLTests(unittest.TestCase):
    def setUp(self):
        import pymol2
        self.pm = pymol2.PyMOL()
        self.pm.start()
        self.cmd = self.pm.cmd
        self.lig = load_script("ligalign")
        self.diff = load_script("struct_diff")
        self.lig.cmd = self.diff.cmd = self.cmd
        self.cmd.load(str(SCRIPTS / "examples/lysozyme_benzene.pdb"), "reference")
        self.cmd.create("benzene_ref", "reference and resn BNZ")
        self.cmd.create("benzene_pose", "benzene_ref")

    def tearDown(self):
        self.pm.stop()

    def globins(self):
        self.cmd.load(str(SCRIPTS / "examples/myoglobin.pdb"), "myoglobin_source")
        self.cmd.load(str(SCRIPTS / "examples/leghemoglobin.pdb"), "leghemoglobin_source")
        self.cmd.create("myoglobin_view", "myoglobin_source")
        self.cmd.create("leghemoglobin_view", "leghemoglobin_source")
        return self.cmd.cealign("myoglobin_view", "leghemoglobin_view", object="globin_alignment")

    def test_inplace_pose_rmsd_preserves_coordinates(self):
        self.cmd.alter("benzene_pose", "name='Q%d'%index")
        self.cmd.sort("benzene_pose")
        self.cmd.translate([0, 0, 2], "benzene_pose")
        before = self.cmd.get_coords("benzene_pose").copy()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rmsd = self.lig.ligalign("benzene_pose", "benzene_ref", method="iso", fit=0)
        self.assertAlmostEqual(rmsd, 2, places=4)
        self.assertIn("12 symmetry-equivalent", output.getvalue())
        np.testing.assert_allclose(self.cmd.get_coords("benzene_pose"), before)

    def test_fitted_geometry_without_transform(self):
        self.cmd.rotate("y", 32, "benzene_pose")
        self.cmd.translate([9, 3, -4], "benzene_pose")
        before = self.cmd.get_coords("benzene_pose").copy()
        rmsd = self.lig.ligalign("benzene_pose", "benzene_ref", method="iso", transform=0, verbose=0)
        self.assertLess(rmsd, 1e-4)
        np.testing.assert_allclose(self.cmd.get_coords("benzene_pose"), before)

    def test_fit_moves_whole_mobile_object_not_reference(self):
        self.cmd.create("complex_pose", "reference")
        before = self.cmd.get_coords("reference").copy()
        self.cmd.translate([3, 4, 0], "complex_pose")
        self.lig.ligalign("complex_pose and resn BNZ", "reference and resn BNZ", method="iso", verbose=0)
        np.testing.assert_allclose(self.cmd.get_coords("complex_pose"), before, atol=1e-3)
        np.testing.assert_allclose(self.cmd.get_coords("reference"), before)

    def test_missing_bond_distance_retry(self):
        self.cmd.unbond("benzene_pose and name C1", "benzene_pose and name C2")
        self.cmd.translate([0, 0, 2], "benzene_pose")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rmsd = self.lig.ligalign("benzene_pose", "benzene_ref", method="iso", fit=0)
        self.assertAlmostEqual(rmsd, 2, places=4)
        self.assertIn("connectivity re-derived", output.getvalue())

    def test_all_mobile_states_and_single_state_target(self):
        self.cmd.create("poses", "benzene_ref", source_state=1, target_state=1)
        self.cmd.create("poses", "benzene_ref", source_state=1, target_state=2)
        self.cmd.translate([0, 0, 2], "poses", state=2)
        self.cmd.frame(2)
        values = self.lig.ligalign("poses", "benzene_ref", method="iso", mobile_state=0, fit=0, verbose=0)
        np.testing.assert_allclose(values, [0, 2], atol=1e-4)

    def test_globin_colouring_report_and_preserved_sources(self):
        self.globins()
        original_b = [a.b for a in self.cmd.get_model("myoglobin_source").atom]
        coordinates = self.cmd.get_coords("leghemoglobin_view").copy()
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "globins.tsv"
            values = self.diff.struct_diff("leghemoglobin_view", "myoglobin_view", atoms="name CA",
                                          method="cealign", maximum=3.0, report=str(report), quiet=1)
            self.assertGreater(sum(v >= 0 for v in values.values()), 100)
            self.assertGreater(max(values.values()), 3.0)
            self.assertGreater(len(report.read_text().splitlines()), 100)
            self.assertNotIn(b"\r", report.read_bytes())
        np.testing.assert_allclose(self.cmd.get_coords("leghemoglobin_view"), coordinates)
        self.assertEqual([a.b for a in self.cmd.get_model("myoglobin_source").atom], original_b)
        self.assertTrue(any(a.b < 0 for a in self.cmd.get_model("myoglobin_view").atom))

    def test_pair_diagnostic_changes_neither_b_nor_coordinates(self):
        self.globins()
        before = self.cmd.get_coords("leghemoglobin_view").copy()
        b = [a.b for a in self.cmd.get_model("leghemoglobin_view").atom]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.diff.struct_diff_pairs("leghemoglobin_view", "myoglobin_view", atoms="name CA",
                                        method="cealign", show="resi 20-23")
        self.assertIn("CA dist", output.getvalue())
        self.assertIn("ASN", output.getvalue())
        np.testing.assert_allclose(self.cmd.get_coords("leghemoglobin_view"), before)
        self.assertEqual([a.b for a in self.cmd.get_model("leghemoglobin_view").atom], b)

    def test_spatial_radius_marks_displaced_residue_unmatched(self):
        self.cmd.create("mobile", "reference and polymer.protein")
        self.cmd.translate([30, 0, 0], "mobile and resi 80")
        self.diff.struct_diff("mobile", "reference", atoms="name CA and (alt ''+A)",
                              method="spatial", radius=.1, quiet=1)
        self.assertTrue(all(a.b == -1 for a in self.cmd.get_model("mobile and resi 80").atom))

    def test_real_pymol_demo_command_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            shutil.copytree(SCRIPTS, folder / "pymol_scripts", ignore=shutil.ignore_patterns("__pycache__"))
            result = subprocess.run([sys.executable, "-m", "pymol", "-cq",
                                     "pymol_scripts/examples/demo_helpers.pml"], cwd=folder,
                                    capture_output=True, text=True, timeout=40)
            log = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, log)
            self.assertNotIn("Traceback", log)
            self.assertNotIn("SyntaxError", log)
            self.assertNotIn(" Error:", log)
            self.assertIn("12 symmetry-equivalent mapping(s)", log)
            self.assertIn("RMSD in place (before fit): 2.0000 A", log)
            self.assertIn("struct_diff: method=cealign", log)
            self.assertTrue((folder / "analysis-results/globins.tsv").is_file(), log)


if __name__ == "__main__":
    unittest.main()
