# 安装与还原

本包适配 Xbox / 微软商店 PC 构建 `1.0.0.0`（Unity `5.6.2p4`），以资源 SHA-256 判断是否兼容。当前为 `v0.1.0-beta.1`：离线校验通过，游戏内显示和实体手柄行为尚待验证。

## 安装

1. **正常退出游戏。** 安装器会检查游戏进程，不会自动结束进程或启动游戏。
2. 右键最外层 `NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip`，选择“全部解压”。
3. 在解压后的普通文件夹 `NITW-Xbox-CN` 中，确认 `2-Install-Chinese.cmd`、`Install.ps1`、`PatchData.zip` 位于同一目录。
4. 双击 `2-Install-Chinese.cmd`。安装器尝试常规 Xbox 目录；没有唯一结果时，按提示填写游戏 `Content` 文件夹路径。可从 Xbox 应用的游戏“管理 → 文件 → 浏览”定位。
5. 显示完成后，关闭安装窗口，自行从 Xbox 启动游戏。

`Install.ps1` 本身就是 PowerShell 脚本；CMD 会自动调用它。内部 `PatchData.zip` 保持原样，不要单独解压。

仅修复输入时运行 `1-Input-Fix.cmd`。汉化模式已经包含输入修复，不用先后安装两次。

## 手动指定路径

在解压后的补丁目录执行，替换示例路径：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Mode Chinese -GameDirectory 'D:\Games\Night in the Woods Win10\Content'
```

`GameDirectory` 是放有 `Night in the Woods.exe` 的 `Content` 文件夹，不是 `Night in the Woods_Data` 子目录。

## 键盘与手柄

- 原版移动：方向键 / WASD。
- 原版交互：C / F；跳跃及菜单确认：X / 空格。
- 本补丁额外加入 Enter 交互/确认。
- 如中文输入法候选栏弹出，请先切到英文输入状态，再测试字母键和空格。
- 未增加鼠标点击菜单的交互方式。
- 有线 DualSense Edge 后备布局：左摇杆移动，× 跳跃/确认，□ 交互，○ 取消，Options 菜单，并补充小游戏和右摇杆映射。此布局尚待实体手柄验收，不保证其他未知设备与蓝牙连接使用相同布局。

## 还原与模式切换

正常退出游戏后，运行 `3-Restore-Original.cmd` 恢复原件。也可直接运行另一个安装入口在输入模式和汉化模式之间切换。

备份位于游戏 `Content/.nitw-xbox-cn-backup`。保留它；恢复时安装器会核对备份和当前资源哈希。安装器先构建全部输出、核验哈希，再复制原件备份和替换；提交阶段失败会尝试从本次事务副本恢复已替换文件。

安装器不修改游戏 EXE、平台 DLL、驱动、存档或 Windows 设置。

## 常见问题

### 提示 `Install.ps1` 不存在

通常是从压缩包预览窗口直接双击 CMD，Windows 只临时解压了 CMD。完整解压最外层安装包，然后从普通文件夹运行，保持三个配套文件在一起。新版入口会在这种情况下显示中文提示。

### 提示缺少 `PatchData.zip`

确认下载的是 Release 中的 `NITW-Xbox-CN-v0.1.0-beta.1-win-x64.zip` 并完整解压。GitHub 自动生成的源码 ZIP 供开发者使用，没有预构建差分数据。

### 提示版本或备份校验不一致

安装器未接受当前资源。核对游戏平台、构建版本和已有其他补丁；不要删除哈希校验来强行安装。若游戏刚刚更新，需要适配新构建。可通过 Xbox 的验证/修复恢复官方文件，再核对兼容性。

### 提示游戏仍在运行

正常退出游戏后重试；工具不会自动结束游戏进程。

### 提示访问被拒绝

保留具体错误，确认所选为 Xbox 提供的可管理 `Content` 目录，而不是凭相似名称找到的其他文件夹。不要为本补丁接管 WindowsApps 所有权、替换认证程序或关闭系统保护。

### 汉化范围

本版主要覆盖剧情与菜单；图片内文字、部分概念画说明和硬编码内容保留原样。游戏内排版、特殊气泡和手柄映射仍需进一步验证。署名和许可见随包 `CREDITS.md` 与 `licenses/`。
