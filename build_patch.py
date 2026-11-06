"""Build resource-only Chinese localization and controller fallback for one verified Xbox PC build."""

import sys, pathlib, json, re, copy, math, struct, hashlib, collections, argparse

BASE = pathlib.Path(__file__).resolve().parent
PROJECT = BASE.parent
import UnityPy, attrs
from PIL import Image, ImageFont, ImageDraw
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

parser = argparse.ArgumentParser(
    description="Build a data-only Chinese localization and USB controller fallback for the Xbox PC build."
)
parser.add_argument("--game-data", type=pathlib.Path, required=True)
parser.add_argument("--translation-source", type=pathlib.Path, required=True)
parser.add_argument("--output-dir", type=pathlib.Path, default=PROJECT / "dist" / "NITW-Xbox-CN")
parser.add_argument("--build-dir", type=pathlib.Path, default=PROJECT / "build")
parser.add_argument("--font", type=pathlib.Path, required=True)
ARGS = parser.parse_args()
ROOT = ARGS.game_data
REPO = ARGS.translation_source
OUT = ARGS.output_dir
OUT.mkdir(parents=True, exist_ok=True)
BUILD = ARGS.build_dir
BUILD.mkdir(parents=True, exist_ok=True)
# Reject a patched or unsupported baseline before loading any game assemblies.
compatibility = json.loads((PROJECT / "metadata/compatibility.json").read_text(encoding="utf-8"))
for expected in compatibility["original_files"]:
    resource = ROOT / expected["path"]
    if (
        not resource.is_file()
        or hashlib.sha256(resource.read_bytes()).hexdigest() != expected["sha256"]
    ):
        raise SystemExit(
            "Unsupported or modified original resource: "
            + expected["path"]
            + ". Restore the supported game build before rebuilding."
        )
GEN = TypeTreeGenerator("5.6.2p4")
GEN.load_local_dll_folder(str(ROOT / "Managed"))
MENU = {
    "Start New Game": "开始新游戏",
    "Continue": "继续游戏",
    "Options": "设置",
    "Extras": "额外内容",
    "Exit": "退出",
    "Back": "返回",
    "Interact": "交互",
    "Jump": "跳跃",
    "Cancel": "取消",
    "Menu": "菜单",
    "Up": "向上",
    "Down": "向下",
    "Left": "向左",
    "Right": "向右",
    "Keyboard Mapping": "键盘映射",
    "Load Defaults": "恢复默认",
    "Resolution": "分辨率",
    "Fullscreen": "全屏",
    "Gamepad Rumble": "手柄震动",
    "Music Volume": "音乐音量",
    "SFX Volume": "音效音量",
    "Text Scroll Volume": "对话音量",
    "Animated Text": "文字动画",
    "On": "开启",
    "Off": "关闭",
    "Yes": "是",
    "No": "否",
    "Save & Quit to Title": "保存并返回标题",
    "Save & Quit to Title?": "保存并返回标题？",
    "Clear Save File": "清除存档",
    "Clear Save File?": "清除存档？",
    "Press X to Continue": "按 X 或空格继续",
    "Press Key to Add/Remove\n5...": "按键以添加或移除\n5...",
    "Clear Save File?\n\n\n(Hold Yes for 3 Seconds to Erase)": "清除存档？\n\n\n（按住“是”三秒）",
}
MENU.update({f"Bass String {i}": f"贝斯弦 {i}" for i in range(1, 5)})
STATS = collections.Counter()
FILES = []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(path):
    e = UnityPy.load(str(path), str(ROOT / "globalgamemanagers.assets"))
    e.typetree_generator = GEN
    return e, next(f for f in e.files.values() if hasattr(f, "objects") and f.name == path.name)


def save_roundtrip(o, d):
    old = o.get_raw_data()
    new = o.save_typetree(d)
    if old != new:
        raise ValueError(f"Unsafe type roundtrip {o.assets_file.name}:{o.path_id}")


def script_name(o):
    try:
        return o.parse_monobehaviour_head().m_Script.deref_parse_as_object().m_ClassName
    except (ValueError, KeyError, FileNotFoundError):
        return None


def input_fix(o):
    d = o.read_typetree()
    save_roundtrip(o, d)
    u = d["_userData"]
    # Keep the wired Sony controller usable alongside a virtual XInput controller.
    u["configVars"]["maxJoysticksPerPlayer"] = 2
    for km in u["keyboardMaps"]:
        if not any(
            a["_actionId"] == 3 and a["_keyboardKeyCode"] == 13 for a in km["actionElementMaps"]
        ):
            a = copy.deepcopy(next(a for a in km["actionElementMaps"] if a["_actionId"] == 3))
            a["_keyboardKeyCode"] = 13
            km["actionElementMaps"].append(a)
    # Unknown controllers have a fixed definition: 32 axes followed by 128 buttons.
    if not any(
        m["hardwareGuidString"] == "00000000-0000-0000-0000-000000000000" for m in u["joystickMaps"]
    ):
        m = copy.deepcopy(u["joystickMaps"][0])
        m.update(
            id=u["joystickMapIdCounter"],
            hardwareGuidString="00000000-0000-0000-0000-000000000000",
            name="DualSense Edge USB fallback",
            actionElementMaps=[],
        )

        def bind(action, element, kind=1, invert=0):
            a = {
                k: 0
                for k in [
                    "_actionCategoryId",
                    "_actionId",
                    "_elementType",
                    "_elementIdentifierId",
                    "_axisRange",
                    "_invert",
                    "_axisContribution",
                    "_keyboardKeyCode",
                    "_modifierKey1",
                    "_modifierKey2",
                    "_modifierKey3",
                ]
            }
            a.update(
                _actionId=action, _elementType=kind, _elementIdentifierId=element, _invert=invert
            )
            m["actionElementMaps"].append(a)

        bind(0, 0, 0)
        bind(1, 1, 0, 1)
        bind(14, 2, 0)
        bind(15, 3, 0, 1)
        # USB HID button 0 Square, 1 Cross, 2 Circle, 3 Triangle, 9 Options.
        for action, button in [
            (2, 1),
            (3, 0),
            (4, 2),
            (5, 9),
            (7, 0),
            (9, 3),
            (10, 1),
            (11, 2),
            (16, 5),
            (17, 4),
            (18, 5),
            (19, 9),
        ]:
            bind(action, 32 + button)
        u["joystickMaps"].append(m)
        u["joystickMapIdCounter"] += 1
    o.save_typetree(d)
    STATS["input_managers"] += 1


def read_translations():
    byname = {}
    global_lines = {}
    for p in (REPO / "TextAsset_UnityEX/Unity_Assets_Files").rglob("*.txt"):
        s = p.read_text(encoding="utf-8-sig")
        name = p.name[:-4]
        byname[name] = s
        for line in s.splitlines():
            mat = re.search(r"\s+#line:([\w.:-]+)", line)
            if mat:
                val = line[: mat.start()].strip()
                val = re.sub(r"^->\s*", "", val)
                if not val.startswith("<<"):
                    global_lines.setdefault(mat.group(1), val)
    return byname, global_lines


TRANSLATED, GLOBAL_LINES = read_translations()


def wrap_chinese(val):
    # The original renderer splits words at ASCII spaces. Small word spaces between
    # Han characters allow native automatic wrapping without changing Yarn grammar.
    def display(text):
        return "".join(
            (
                t
                if t.startswith(("{", "[", "<<"))
                else re.sub(r"([\u3400-\u9fff])(?=[\u3400-\u9fff])", r"\1 ", t)
            )
            for t in re.split(r"(\{[^}]*\}|\[[^\]]*\]|<<.*?>>)", text)
        )

    if val.startswith("[[") and val.endswith("]]") and "|" in val:
        label, target = val[2:-2].rsplit("|", 1)
        return "[[" + display(label) + "|" + target + "]]"
    return display(val)


def flow_tokens(text):
    tokens = []
    for m in re.finditer(r"<<.*?>>|\[\[.*?\]\]", text):
        s = m.group()
        if s.startswith("[[") and "|" in s:
            s = "[[" + s[2:-2].rsplit("|", 1)[-1] + "]]"
        tokens.append(s)
    return tokens


def translate_yarn(original, cn):
    lookup = {}
    for l in cn.splitlines():
        m = re.search(r"\s+#line:([\w.:-]+)", l)
        if m:
            lookup[m.group(1)] = re.sub(r"^->\s*", "", l[: m.start()].strip())
    out = []
    translated = 0
    available = 0
    for line in original.splitlines(keepends=True):
        m = re.search(r"\s+#line:([\w.:-]+)", line)
        if m:
            available += 1
            val = lookup.get(m.group(1))
            if val and any("\u3400" <= c <= "\u9fff" for c in val):
                prefix = line[: m.start()]
                indent = re.match(r"\s*", prefix).group()
                is_option = prefix.lstrip().startswith("->")
                # Speaker identifiers and all commands remain those of the Xbox original.
                speaker = re.match(r"^(\w+):\s*", prefix.strip())
                if speaker:
                    val = re.sub(r"^\w+:\s*", "", val)
                    val = speaker.group(1) + ": " + val
                original_links = re.findall(r"\[\[([^\]]+)\]\]", prefix)
                translated_links = re.findall(r"\[\[([^\]]+)\]\]", val)
                if len(original_links) == len(translated_links) and original_links:
                    link_index = [0]

                    def original_target(match):
                        original_link = original_links[link_index[0]]
                        link_index[0] += 1
                        if "|" in original_link and "|" in match.group(1):
                            return (
                                "[["
                                + match.group(1).rsplit("|", 1)[0]
                                + "|"
                                + original_link.rsplit("|", 1)[1]
                                + "]]"
                            )
                        return match.group()

                    val = re.sub(r"\[\[([^\]]+)\]\]", original_target, val)
                oldcmd = flow_tokens(prefix)
                newcmd = flow_tokens(val)
                if oldcmd == newcmd:
                    val = wrap_chinese(val)
                    line = indent + ("-> " if is_option else "") + val + line[m.start() :]
                    translated += 1
        out.append(line)
    result = "".join(out)
    # Commands, links, node IDs and branching are never replaced by another build's script.
    if flow_tokens(original) != flow_tokens(result):
        raise ValueError("Translation changed original control flow")
    for pattern in [r"<<.*?>>", r"^title:.*$", r"#line:[\w.:-]+"]:
        if re.findall(pattern, original, re.M) != re.findall(pattern, result, re.M):
            raise ValueError("Translation changed original node, command or line identifiers")
    STATS["dialogue_lines_available"] += available
    STATS["dialogue_lines_translated"] += translated
    return result


def make_static_font(chars):
    path = BUILD / "NITW-NotoSansSC.ttf"
    f = TTFont(ARGS.font)
    f = instantiateVariableFont(f, {"wght": 500}, inplace=True)
    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    sub = subset.Subsetter(options=options)
    sub.populate(text="".join(chars) + "".join(chr(i) for i in range(32, 256)))
    sub.subset(f)
    f.save(path)
    return path


def clone_object(template, pathid, tree):
    obj = attrs.evolve(template, path_id=pathid, data=None)
    template.assets_file.objects[pathid] = obj
    obj.save_typetree(tree)
    return obj


def inject_glyphs(sf, chars):
    fonts = []
    for o in list(sf.objects.values()):
        if o.type.name == "MonoBehaviour":
            try:
                if script_name(o) == "SpriteFont":
                    d = o.read_typetree()
                    save_roundtrip(o, d)
                    fonts.append((o, d))
            except ValueError:
                raise
            except:
                pass
    if not fonts:
        return {}
    all_existing = {c["character"] for o, d in fonts for c in d["charDatas"]}
    chars = sorted(c for c in chars if c not in all_existing and not c.isspace() and ord(c) > 127)
    size = 48
    cols = 80
    rows = math.ceil(len(chars) / cols)
    height = 2 ** math.ceil(math.log2(max(1, rows * size)))
    width = 4096
    atlas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(atlas)
    font = ImageFont.truetype(str(BUILD / "NITW-NotoSansSC.ttf"), 42)
    for i, c in enumerate(chars):
        x = (i % cols) * size
        y = (i // cols) * size
        box = draw.textbbox((0, 0), c, font=font)
        draw.text(
            (
                x + (size - (box[2] - box[0])) / 2 - box[0],
                y + (size - (box[3] - box[1])) / 2 - box[1],
            ),
            c,
            font=font,
            fill="white",
        )
    atlas.save(BUILD / "glyph-atlas.png")
    template = next(o for o in sf.objects.values() if o.type.name == "Sprite")
    tex_template = next(o for o in sf.objects.values() if o.type.name == "Texture2D")
    nextid = max(sf.objects) + 1
    td = tex_template.read_typetree()
    td.update(
        m_Name="NITW_CN_Atlas",
        m_Width=width,
        m_Height=height,
        m_CompleteImageSize=width * height * 4,
        m_TextureFormat=4,
        m_MipCount=1,
        m_IsReadable=False,
    )
    td["m_TextureSettings"].update(m_FilterMode=1, m_Aniso=1, m_WrapMode=1)
    td["m_StreamData"] = {"offset": 0, "size": 0, "path": ""}
    td["image data"] = atlas.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    texture = clone_object(tex_template, nextid, td)
    nextid += 1
    mapping = {}
    base = template.read_typetree()
    for i, c in enumerate(chars):
        x = (i % cols) * size
        y = height - ((i // cols) + 1) * size
        s = copy.deepcopy(base)
        s["m_Name"] = f"CN_U{ord(c):04X}"
        s["m_Rect"] = {"x": 0.0, "y": 0.0, "width": float(size), "height": float(size)}
        s["m_Offset"] = {"x": 0.0, "y": 0.0}
        s["m_Border"] = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 0.0}
        s["m_PixelsToUnits"] = float(size)
        s["m_Pivot"] = {"x": 0.5, "y": 0.5}
        s["m_IsPolygon"] = False
        rd = s["m_RD"]
        rd["texture"] = {"m_FileID": 0, "m_PathID": texture.path_id}
        rd["alphaTexture"] = {"m_FileID": 0, "m_PathID": 0}
        rd["textureRect"] = {
            "x": float(x),
            "y": float(y),
            "width": float(size),
            "height": float(size),
        }
        rd["textureRectOffset"] = {"x": 0.0, "y": 0.0}
        rd["atlasRectOffset"] = {"x": 0.0, "y": 0.0}
        rd["settingsRaw"] = 0
        rd["uvTransform"] = {
            "x": float(size),
            "y": x + size / 2,
            "z": float(size),
            "w": y + size / 2,
        }
        rd["m_SubMeshes"] = [
            {
                "firstByte": 0,
                "indexCount": 6,
                "topology": 0,
                "firstVertex": 0,
                "vertexCount": 4,
                "localAABB": {
                    "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "m_Extent": {"x": 0.5, "y": 0.5, "z": 0.0},
                },
            }
        ]
        rd["m_IndexBuffer"] = struct.pack("<6H", 0, 1, 2, 2, 1, 3)
        vd = rd["m_VertexData"]
        vd["m_CurrentChannels"] = 9
        vd["m_VertexCount"] = 4
        vd["m_Channels"] = [{"stream": 0, "offset": 0, "format": 0, "dimension": 3}] + [
            {"stream": 0, "offset": 0, "format": 0, "dimension": 0} for _ in range(7)
        ]
        vd["m_Channels"][3] = {"stream": 0, "offset": 12, "format": 0, "dimension": 2}
        vertices = [
            (-0.5, -0.5, 0, x / width, y / height),
            (-0.5, 0.5, 0, x / width, (y + size) / height),
            (0.5, -0.5, 0, (x + size) / width, y / height),
            (0.5, 0.5, 0, (x + size) / width, (y + size) / height),
        ]
        vd["m_DataSize"] = b"".join(struct.pack("<5f", *v) for v in vertices)
        clone_object(template, nextid, s)
        mapping[c] = nextid
        nextid += 1
    for o, d in fonts:
        d["spaceWidth"] = 0.045
        for c, pid in mapping.items():
            d["charDatas"].append(
                {
                    "character": c,
                    "additionalCharacters": "",
                    "width": 0.95,
                    "frames": [{"m_FileID": 0, "m_PathID": pid}],
                }
            )
        o.save_typetree(d)
        STATS["sprite_fonts"] += 1
    STATS["glyphs"] = len(mapping)
    return mapping


def add_patch(filename, original, new, mode):
    dest = BUILD / mode
    dest.mkdir(exist_ok=True)
    (dest / filename).write_bytes(new)
    FILES.append(
        {
            "path": filename,
            "mode": mode,
            "original_sha256": sha(original),
            "target_sha256": sha(new),
            "original_size": len(original),
            "target_size": len(new),
        }
    )


def main():
    # First pass: translate display lines only; original script structure is preserved.
    display = []
    modified = []
    for path in sorted(ROOT.glob("*.assets")):
        if path.name == "globalgamemanagers.assets":
            continue
        env, sf = load(path)
        changed = False
        for o in list(sf.objects.values()):
            if o.type.name == "TextAsset":
                d = o.read_typetree()
                cn = TRANSLATED.get(d["m_Name"])
                if cn:
                    s = translate_yarn(d["m_Script"], cn)
                    if s != d["m_Script"]:
                        d["m_Script"] = s
                        o.save_typetree(d)
                        changed = True
                        STATS["yarn_assets"] += 1
                    display.append(s)
            elif o.type.name == "TextMesh":
                d = o.read_typetree()
                s = MENU.get(d["m_Text"])
                if s:
                    d["m_Text"] = s
                    o.save_typetree(d)
                    changed = True
                    STATS["menu_labels"] += 1
        if changed:
            (BUILD / path.name).write_bytes(sf.save())
            modified.append(path.name)
        if len(modified) % 20 == 0 and changed:
            print("Translated assets", len(modified), flush=True)
    # Translate scene menus; font and input objects are handled in the final pass.
    for path in sorted(ROOT.glob("level*")):
        if not path.is_file():
            continue
        env, sf = load(path)
        changed = False
        for o in list(sf.objects.values()):
            if o.type.name == "TextMesh":
                d = o.read_typetree()
                s = MENU.get(d["m_Text"])
                if s:
                    d["m_Text"] = s
                    o.save_typetree(d)
                    changed = True
                    STATS["menu_labels"] += 1
        if changed:
            (BUILD / path.name).write_bytes(sf.save())
            modified.append(path.name)
    chars = set("".join(display) + "".join(MENU.values()))
    chars = {c for c in chars if ord(c) >= 32}
    fontpath = make_static_font(chars)
    fontdata = list(fontpath.read_bytes())
    # Input-only assets do not include any localization changes.
    for filename in ["level0", "sharedassets0.assets"]:
        env, sf = load(ROOT / filename)
        for o in list(sf.objects.values()):
            if o.type.name == "MonoBehaviour":
                try:
                    if script_name(o) == "InputManager":
                        input_fix(o)
                except ValueError:
                    raise
                except:
                    pass
        add_patch(filename, (ROOT / filename).read_bytes(), sf.save(), "input")
    # Main atlas is referenced by all duplicated font objects.
    env, sf = load(BUILD / "sharedassets0.assets")
    mapping = inject_glyphs(sf, chars)
    for o in list(sf.objects.values()):
        if o.type.name == "Font":
            d = o.read_typetree()
            d["m_FontData"] = fontdata
            if "m_FontNames" in d:
                d["m_FontNames"] = ["Noto Sans SC"]
            o.save_typetree(d)
            STATS["menu_fonts"] += 1
        elif o.type.name == "MonoBehaviour":
            try:
                if script_name(o) == "InputManager":
                    input_fix(o)
            except ValueError:
                raise
            except:
                pass
    (BUILD / "sharedassets0.assets").write_bytes(sf.save())
    # Shared boot objects carry separate font arrays; retain their external file IDs.
    env, sf = load(ROOT / "level0")
    for o in list(sf.objects.values()):
        if o.type.name == "MonoBehaviour":
            try:
                name = script_name(o)
                if name == "InputManager":
                    input_fix(o)
                elif name == "SpriteFont":
                    d = o.read_typetree()
                    save_roundtrip(o, d)
                    d["spaceWidth"] = 0.045
                    fileid = next(c["frames"][0]["m_FileID"] for c in d["charDatas"] if c["frames"])
                    for c, pid in mapping.items():
                        d["charDatas"].append(
                            {
                                "character": c,
                                "additionalCharacters": "",
                                "width": 0.95,
                                "frames": [{"m_FileID": fileid, "m_PathID": pid}],
                            }
                        )
                    o.save_typetree(d)
                    STATS["sprite_fonts"] += 1
            except ValueError:
                raise
            except:
                pass
    (BUILD / "level0").write_bytes(sf.save())
    if "level0" not in modified:
        modified.append("level0")
    for name in modified:
        add_patch(name, (ROOT / name).read_bytes(), (BUILD / name).read_bytes(), "chinese")
    (BUILD / "manifest-files.json").write_text(
        json.dumps(FILES, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (BUILD / "stats.json").write_text(
        json.dumps(dict(STATS), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (BUILD / "glyph-map.json").write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")
    print(dict(STATS), flush=True)


if __name__ == "__main__":
    main()
