import ast
import re
import subprocess
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
    def test_reconstructed_final_files_and_upstream_anchors(self):
        prep_text = (CI_DIR / "prepare.py").read_text(encoding="utf-8")
        patch_order = re.findall(r'"(voidgram-[^"]+\.patch)"', prep_text)
        self.assertGreaterEqual(len(patch_order), 45)

        stripped_lines = []
        for pname in patch_order:
            pfile = ROOT_DIR / "patches" / pname
            for line in pfile.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    stripped_lines.append(line[1:])
                elif line.startswith(" "):
                    stripped_lines.append(line[1:])
        stripped_all = "\n".join(stripped_lines)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            new_files = set()
            for pname in patch_order:
                raw = (ROOT_DIR / "patches" / pname).read_text(encoding="utf-8", errors="ignore")
                chunks = re.split(r"(?=^diff --git )", raw, flags=re.M)
                filtered = []
                for ch in chunks:
                    if not ch.startswith("diff --git "):
                        continue
                    m = re.match(r"diff --git a/(\S+) b/(\S+)", ch)
                    if not m or not m.group(2).endswith(".swift"):
                        continue
                    rel = m.group(2)
                    if "new file mode" in ch:
                        new_files.add(rel)
                    if rel in new_files:
                        filtered.append(ch)
                if filtered:
                    patch_data = "".join(filtered) + ("\n" if not filtered[-1].endswith("\n") else "")
                    subprocess.run(
                        ["git", "apply", "--recount"],
                        input=patch_data.encode("utf-8"),
                        cwd=repo,
                        check=True,
                        stderr=subprocess.DEVNULL,
                    )

            src_text = (CI_DIR / "nowzen_enhancements.py").read_text(encoding="utf-8")
            tree = ast.parse(src_text)

            synthetic_upstream: dict[str, str] = {}
            checked_count = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("_enhance_"):
                    var_to_rel = {}
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                            if isinstance(stmt.value, ast.BinOp) and isinstance(stmt.value.right, ast.Constant):
                                var_to_rel[stmt.targets[0].id] = stmt.value.right.value
                            elif isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                var_to_rel[stmt.targets[0].id] = stmt.value.value
                        if isinstance(stmt, ast.Call) and getattr(stmt.func, "id", "") == "_replace_once":
                            rel = var_to_rel[stmt.args[0].id]
                            old = ast.literal_eval(stmt.args[1])
                            label = ast.literal_eval(stmt.args[3])
                            checked_count += 1
                            fpath = repo / rel
                            if fpath.is_file():
                                self.assertIn(
                                    old,
                                    fpath.read_text(encoding="utf-8"),
                                    f"Anchor '{label}' failed against final reconstructed {rel}",
                                )
                            else:
                                self.assertIn(
                                    old,
                                    stripped_all,
                                    f"Upstream anchor '{label}' missing from patches for {rel}",
                                )
                                synthetic_upstream.setdefault(rel, "")
                                synthetic_upstream[rel] += "\n" + old + "\n"

            # Also seed ChatListItem.swift's double avatarDiameter anchor for full apply run
            cl_item_rel = "submodules/ChatListUI/Sources/Node/ChatListItem.swift"
            diam_anchor = (
                "            // VoidGram classic design: the old list's smaller avatars; the text starts at 70 pt.\n"
                "            if AyuAppearancePlus.launchClassicDesign, !item.useCommunityViewLayout {\n"
                "                avatarDiameter = min(46.0, avatarDiameter)\n"
                "            }"
            )
            self.assertIn(diam_anchor, stripped_all)
            synthetic_upstream[cl_item_rel] = (
                diam_anchor + "\n\n" + diam_anchor + "\n" + synthetic_upstream.get(cl_item_rel, "")
            )

            for rel, content in synthetic_upstream.items():
                target = repo / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            self.assertGreaterEqual(checked_count, 25)
            nowzen_enhancements.apply_nowzen_enhancements(repo)

            # Post-apply assertions on key features
            self.assertIn(
                "NowzenOnlineTracker",
                (repo / "submodules/TelegramUI/Sources/AyuHistoryNotifications.swift").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "NowzenChatSimulator",
                (repo / "submodules/TelegramUI/Sources/AyuChatLock.swift").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Первое сообщение в чате",
                (repo / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "avatarDiameter = min(50.0, avatarDiameter)",
                (repo / cl_item_rel).read_text(encoding="utf-8"),
            )

            import preflight
            for rel in sorted(new_files | set(synthetic_upstream.keys())):
                fpath = repo / rel
                if fpath.is_file():
                    errs = preflight.contract_errors(fpath.read_text(encoding="utf-8"), rel)
                    self.assertEqual(errs, [], f"preflight.contract_errors failed for {rel}: {errs}")

            # Ensure no replacement string in nowzen_enhancements.py introduces trailing whitespace (git diff --check)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_replace_once":
                    new_str = ast.literal_eval(node.args[2])
                    label = ast.literal_eval(node.args[3])
                    for idx, line in enumerate(new_str.splitlines(), 1):
                        self.assertEqual(line, line.rstrip(" \t"), f"Trailing whitespace in '{label}' line {idx}")


if __name__ == "__main__":
    unittest.main()
