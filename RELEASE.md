# GitHub 发布

建议仓库名：`nitw-xbox-cn`。建议简介：

> Night in the Woods Xbox PC 简体中文适配、输入修复与可回滚差分安装器。

首版标签：`v0.1.0-beta.1`。标题：`v0.1.0-beta.1 · Xbox PC 剧情与菜单汉化测试版`。发布时勾选 **Set as a pre-release**。

## 源码仓库

将仓库根目录的文件和文件夹上传，包括 `src/`、`installer/`、`scripts/`、`tests/`、`metadata/`、`docs/`、`.github/`、许可证和根 README。保留 `.gitignore`、`.gitattributes` 等点开头的文件。

不提交 `build/`、`dist/`、`third_party/`、游戏原件、存档、备份或 Python 环境。仓库里已经放好忽略规则。

## Release 附件

上传这两个文件：

- `NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip`
- `NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip.sha256`

GitHub 自动生成的 Source code 下载供开发者使用；可安装补丁作为单独附件。不要把完整游戏资源构建目录作为附件。

说明可直接使用 [RELEASE_NOTES.md](../RELEASE_NOTES.md)。首版应保持“离线验证通过、尚未完成游戏内验收”的表述；经过实际测试后再按具体范围补充测试记录。

GitHub 官方说明：[关于 Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)、[管理 Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)。
