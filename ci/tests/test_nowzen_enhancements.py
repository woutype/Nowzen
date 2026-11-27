import ast
import sys
import tempfile
import unittest
from pathlib import Path

CI_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = CI_DIR.parent
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

import nowzen_enhancements


class TestNowzenEnhancements(unittest.TestCase):
    def test_all_anchors_exist_in_patches(self):
        src_text = (CI_DIR / "nowzen_enhancements.py").read_text(encoding="utf-8")
        tree = ast.parse(src_text)
        anchors = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_replace_once":
                old = ast.literal_eval(node.args[1])
                label = ast.literal_eval(node.args[3])
                anchors.append((label, old))

        self.assertGreaterEqual(len(anchors), 20)

        stripped_lines = []
        for patch_file in sorted((ROOT_DIR / "patches").glob("*.patch")):
            for line in patch_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    stripped_lines.append(line[1:])
                elif line.startswith(" "):
                    stripped_lines.append(line[1:])
        stripped_text = "\n".join(stripped_lines)

        missing = [label for label, old in anchors if old not in stripped_text]
        self.assertEqual(missing, [], f"Missing anchors in patches: {missing}")

    def test_apply_enhancements_transforms_synthetic_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Extract minimal synthetic files matching every _replace_once anchor
            src_text = (CI_DIR / "nowzen_enhancements.py").read_text(encoding="utf-8")
            tree = ast.parse(src_text)

            file_contents = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("_enhance_"):
                    # Map variable names like path, privacy_path, etc. to relative paths
                    var_to_rel = {}
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                            if isinstance(stmt.value, ast.BinOp) and isinstance(stmt.value.right, ast.Constant):
                                var_to_rel[stmt.targets[0].id] = stmt.value.right.value
                        if isinstance(stmt, ast.Call) and getattr(stmt.func, "id", "") == "_replace_once":
                            var_name = stmt.args[0].id
                            rel = var_to_rel[var_name]
                            old = ast.literal_eval(stmt.args[1])
                            file_contents.setdefault(rel, "")
                            if old not in file_contents[rel]:
                                file_contents[rel] += "\n" + old + "\n"

            for rel, content in file_contents.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            nowzen_enhancements.apply_nowzen_enhancements(root)

            # Verify key invariants after transformation
            app_delegate = (root / "submodules/TelegramUI/Sources/AppDelegate.swift").read_text(encoding="utf-8")
            self.assertIn("com.nowzen.enterGhostMode", app_delegate)
            self.assertNotIn("AyuExtras.isOn(.blurInAppSwitcher)", app_delegate)

            history = (root / "submodules/TelegramCore/Sources/AyuGram/AyuMessageHistory.swift").read_text(encoding="utf-8")
            self.assertIn("let preservedMedia = previous.media", history)
            self.assertIn("media: preservedMedia", history)

            extras = (root / "submodules/SettingsUI/Sources/AyuExtrasController.swift").read_text(encoding="utf-8")
            self.assertIn(".link(4, 40,", extras)
            self.assertNotIn(".link(4, 35,", extras)


if __name__ == "__main__":
    unittest.main()
