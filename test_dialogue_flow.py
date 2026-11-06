"""Exercise the actual pure translation functions without loading game libraries."""

import ast
import collections
from pathlib import Path
import re
import unittest

PROJECT = Path(__file__).resolve().parent.parent


class DialogueFlowTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((PROJECT / "src/build_patch.py").read_text(encoding="utf-8"))
        functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in ("wrap_chinese", "flow_tokens", "translate_yarn")
        ]
        namespace = {"re": re, "STATS": collections.Counter()}
        exec(
            compile(ast.Module(body=functions, type_ignores=[]), "translation-functions", "exec"),
            namespace,
        )
        self.translate = namespace["translate_yarn"]
        self.flow = namespace["flow_tokens"]

    def test_original_choice_target_case_and_line_id_are_preserved(self):
        original = "title: Root\n---\n[[Example choice|KeepThisCase]] #line:abc123\n===\n"
        translated = "title: Root\n---\n[[中文选项|keepthiscase]] #line:abc123\n===\n"
        result = self.translate(original, translated)
        self.assertIn("|KeepThisCase]] #line:abc123", result)
        self.assertNotIn("|keepthiscase]]", result)
        self.assertEqual(self.flow(original), self.flow(result))

    def test_translator_cannot_replace_original_script_command(self):
        original = "title: Root\n---\nMae: Hello <<wait 1>> #line:abc123\n===\n"
        translated = "Mae: 你好 <<wait 9>> #line:abc123\n"
        self.assertEqual(self.translate(original, translated), original)

    def test_original_speaker_conditions_and_branch_indentation_are_preserved(self):
        original = "title: Root\n---\n<<if $flag is 1>>\n    -> Example #line:one\n        Mae: Hello #line:two\n<<endif>>\n===\n"
        translated = "-> 示例 #line:one\nOtherSpeaker: 你好 #line:two\n"
        result = self.translate(original, translated)
        self.assertIn("    -> 示 例 #line:one", result)
        self.assertIn("        Mae: 你 好 #line:two", result)
        self.assertEqual(self.flow(original), self.flow(result))


if __name__ == "__main__":
    unittest.main()
