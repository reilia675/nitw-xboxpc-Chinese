# 署名与资源来源

## 对白翻译

中文对白和选项译文来自**识渡汉化组**的公开工程：

- 项目：[Know-Team/NITW_zh-Hans-CN_l10n](https://github.com/Know-Team/NITW_zh-Hans-CN_l10n)
- 首版使用的提交：`699d5936d20461aed4328dc82ca0449e75527c64`
- 原版权声明：`Copyright (c) 2022 Sunshine-Planet and UltimateLin`
- 许可证原文：[licenses/Know-Team-MIT.txt](licenses/Know-Team-MIT.txt)
- 完整参与者名单与翻译致谢以[上游 README](https://github.com/Know-Team/NITW_zh-Hans-CN_l10n#readme)为准。

本项目新增 Xbox PC 版资源适配、字形生成、输入后备映射、差分打包、校验和安装/还原脚本。**不将原译文署名为本项目原创翻译。** 上游声明的适用平台为 Steam/Epic；本 Xbox 适配由本项目维护，不代表上游团队提供兼容承诺或支持。

上游项目提到的替换程序集、3DM 字库实现及图片贴图均未纳入这个版本。

## 中文字体

- 字体：Noto Sans SC（Google Fonts）。
- 来源：[google/fonts/ofl/notosanssc](https://github.com/google/fonts/tree/main/ofl/notosanssc)。
- 处理：生成静态字重实例、裁剪字形子集，并渲染为游戏原生 Sprite 字形；菜单字体以子集形式嵌入资源差分。
- 许可证：[licenses/NotoSansSC-OFL.txt](licenses/NotoSansSC-OFL.txt)，SIL Open Font License 1.1。
- 原始字体 SHA-256 记录在 [metadata/Provenance.json](metadata/Provenance.json)。

## 游戏与项目代码

Night in the Woods 的原始程序、美术、声音、剧情及相关商标归各自权利人所有。本项目是非官方兼容补丁，不附带游戏主程序、平台 DLL 或完整的原始游戏资源；需要用户已有的兼容版本游戏才能应用。

本项目适配代码和安装工具采用仓库根目录的 [MIT 许可证](LICENSE)。该许可证仅覆盖本项目有权许可的代码与文档，不替代游戏、上游翻译或字体各自的许可。
