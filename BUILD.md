# 从源码构建

构建需要 Windows x64、Python 3.12、**兼容版本且未打补丁的本地游戏**。游戏、翻译源码和字体均由构建者自行获取；本仓库不附带游戏文件。

## 准备

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Path third_party -Force
git clone https://github.com/Know-Team/NITW_zh-Hans-CN_l10n.git third_party/know-localization
git -C third_party/know-localization checkout 699d5936d20461aed4328dc82ca0449e75527c64
Invoke-WebRequest 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf' -OutFile third_party/NotoSansSC.ttf
```

首版字体源文件 SHA-256 为：

```text
a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da
```

可用 `Get-FileHash third_party/NotoSansSC.ttf -Algorithm SHA256` 核对。上游字体、依赖或构建库变化都可能改变生成结果；新的构建应重新验证并更新来源记录，不能仅凭版本号宣称与首版逐字节相同。完整来源见 `metadata/Provenance.json`。

## 生成资源与差分

将示例游戏目录改为自己安装的 `Night in the Woods_Data` 路径：

```powershell
.\.venv\Scripts\python.exe src/build_patch.py --game-data 'D:\Games\Night in the Woods Win10\Content\Night in the Woods_Data' --translation-source third_party/know-localization --font third_party/NotoSansSC.ttf
.\.venv\Scripts\python.exe src/pack_patch.py --game-data 'D:\Games\Night in the Woods Win10\Content\Night in the Woods_Data'
```

默认中间目录是 `build/`，默认差分输出是 `dist/NITW-Xbox-CN/`。它们均由 `.gitignore` 排除。构建器先核对 `metadata/compatibility.json` 中的全部原件哈希；已经汉化或不支持的资源会被拒绝。

`build_patch.py` 会加载该游戏目录中的托管程序集来生成 Unity 类型树，并读取资源；不会启动游戏或覆盖安装目录。转换输出中的完整本地资源仅供构建使用，不提交到仓库或发布附件。

`pack_patch.py` 按复制/新增指令生成资源差分，并实际重建每个输出核对一致性。它同时核对原件和构建产物 SHA-256，避免用错误的基线打包。

## 生成用户安装包

```powershell
.\.venv\Scripts\python.exe scripts/package_release.py --patch-data dist/NITW-Xbox-CN/PatchData.zip
```

生成：

```text
dist/release-assets/NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip
dist/release-assets/NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip.sha256
```

打包器会复制安装器模板，注入 `PatchData.zip` 的实际校验值，附带说明、来源、许可、元数据与文件哈希清单。仓库内 `installer/Install.ps1` 中的 `__ARCHIVE_SHA__` 是构建占位符；用户应使用已打包的 Release 安装器。

## 验证

```powershell
python -m unittest discover -s tests -v
```

标准库测试覆盖差分往返、错误基线保护以及中文文本替换时的命令/节点保护，不需要游戏资源。游戏资源的实际重建和安装器集成验证需要本地兼容游戏；详见 [TESTING.md](TESTING.md)。

## 适配其他版本

新增版本要核对 Unity 类型树往返、菜单与脚本结构、原始分支目标、字体引用、输入库未知控制器定义和实际游戏行为。应生成独立的兼容清单与测试记录，保留原版本支持信息。修改哈希清单本身不会使不同构建自动兼容。
