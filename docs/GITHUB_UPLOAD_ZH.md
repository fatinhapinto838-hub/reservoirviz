# 上传到 GitHub

建议仓库名：`reservoirviz`。建议描述：

> Open-source CSV visualization and validation for reservoir simulation time series, built with Python, Streamlit, and Plotly.

## 使用网页上传

1. 解压交付的 ZIP，进入 `reservoirviz` 文件夹。
2. 在 [GitHub 新建仓库](https://github.com/new) 创建 Public 仓库。可以先不勾选生成 README、许可证或 `.gitignore`，项目已包含这些文件。
3. 在空仓库选择“uploading an existing file”，或在仓库的“Add file → Upload files”上传。
4. 拖入 `reservoirviz` 文件夹内的全部内容。上传后仓库根目录应直接出现 `app.py`、`README.md`、`requirements.txt`、`reservoirviz/` 等，避免多套一层目录。
5. 在 Mac 访达按 **Command+Shift+.** 显示隐藏文件，检查 `.github/`、`.streamlit/` 和 `.gitignore` 也被上传。它们分别提供自动检查、界面配置及忽略规则。
6. 提交说明可填写 `feat: initial ReservoirViz v0.1.0`，然后保存。
7. 检查 README 的截图是否显示，进入 Actions 查看自动测试实际结果。

ZIP 是传输包，GitHub 不会把上传的 ZIP 自动展开成代码仓库。请先解压，再上传文件。

## 使用 Git（更适合后续维护）

在解压后的项目目录打开终端，把下面命令中的仓库地址换成自己新建仓库的地址：

```bash
git init
git add .
git commit -m "feat: initial ReservoirViz v0.1.0"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

首次使用 Git 时可能需要设置提交姓名、邮箱，以及完成 GitHub 身份验证。`YOUR_REPOSITORY_URL` 是占位说明，不要原样运行。也可使用 [GitHub Desktop](https://desktop.github.com/) 选择此文件夹并发布。

## 上传后逐项确认

- README 能打开，截图能显示。
- `app.py` 位于仓库根目录。
- `LICENSE`、样例、文档和测试均在仓库中。
- Actions 实际通过后，再填写本仓库的 CI 徽章；当前未放置虚构的成功徽章。
- 真实导出数据仅在获得公开许可后加入；私人文件存放在被忽略的 `user_data/`。

可以在 Releases 创建 `v0.1.0`，说明功能和限制，使用 `CHANGELOG.md` 中的实际变更内容。版本包已准备好，但 GitHub 发布动作由仓库维护者完成。

## 可选：公开演示

本地版本稳定后，可阅读 [Streamlit Community Cloud 部署指南](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)。选择自己的仓库、分支 `main` 和入口 `app.py`，使用 Python 3.12。部署后应重新检查上传、图表和下载功能；本地通过不代表远端已经部署成功。

公开演示中的用户文件会上传到部署服务器。应向试用者说明这一点，并优先使用可公开的样例。
