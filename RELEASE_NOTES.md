# v0.1.0-beta.1 · Xbox PC 剧情与菜单汉化测试版

非官方的 Night in the Woods Xbox / 微软商店 PC 版中文适配，基于识渡汉化组公开译文。

## 下载

请下载附件 `NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip`，完整解压后运行 `2-Install-Chinese.cmd`。压缩包内保留 `Install.ps1` 与 `PatchData.zip`。仅修复输入运行 `1-Input-Fix.cmd`，恢复原版运行 `3-Restore-Original.cmd`。

## 内容

- 23,969 条含中文的对白与选项，127 个剧情文本资源。
- 152 处菜单文字、2,764 个中文及扩展字形、四个菜单字体资源。
- 保留 Xbox 原始剧情命令和分支目标，修正三个上游选项节点大小写适配问题。
- 增加 Enter 确认/交互，以及有线 DualSense Edge 的未知控制器后备映射。
- 原件 SHA-256 校验、资源备份、模式切换和恢复；安装入口支持常规路径查找与手动填写目录。

## 兼容

已适配 Xbox PC 包版本 `1.0.0.0`、Unity `5.6.2p4`。**以兼容清单中的资源哈希为准**；不同构建会停止安装。

## 测试状态

已通过离线资源、差分重建及模拟安装/还原校验。**尚未完成游戏内字体、完整剧情和实体手柄验收。** 此版本标记为预发布测试版。

日记、海报等图片文字、部分概念画说明和硬编码内容仍保留原样。其他平台、其他控制器和蓝牙连接未声明兼容。

## 署名

对白翻译：[识渡汉化组](https://github.com/Know-Team/NITW_zh-Hans-CN_l10n)，MIT；字体：[Noto Sans SC](https://github.com/google/fonts/tree/main/ofl/notosanssc)，SIL OFL 1.1。本项目负责 Xbox 适配与工具，完整许可和署名随包提供。

需要用户已有的兼容游戏安装。安装包不含游戏主程序、平台 DLL 或完整的原始游戏资源。
