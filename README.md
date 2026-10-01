# ChipSeeker Downloader

ChipSeeker Downloader downloads PDF tasks exported by ChipSeeker Online on the user's own computer. ChipSeeker does not proxy or store the PDF files.

ChipSeeker Downloader 用于在用户自己的电脑上处理在线版导出的论文下载任务。PDF 不经过 ChipSeeker 服务器。

The downloader opens a visible Microsoft Edge or Google Chrome window. If IEEE redirects to a login or landing page, finish institutional login, VPN setup, or page navigation in that window, then return to the terminal and retry.

## Install on Windows

The easiest method is to download and extract the repository, then double-click `Install ChipSeeker Downloader.cmd` once.

```powershell
git clone https://github.com/Yixuan-Miao/ChipSeeker-Downloader.git
cd ChipSeeker-Downloader
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer creates an isolated Python environment and associates `.csdl` files with the downloader. It does not require administrator access and does not install a browser extension.

## Use

1. Search and select papers on ChipSeeker Online.
2. Click `Batch Download Task (.csdl)`.
3. Double-click the downloaded `.csdl` file.
4. Keep the visible download browser open. Complete IEEE login when requested.
5. PDFs are saved under `Downloads\ChipSeeker\<task name>`.

If the downloader is started without a task file, it automatically uses the newest `.csdl` file in the browser Downloads folder.

Command-line use:

```powershell
.\.venv\Scripts\python.exe .\downloader.py "C:\Users\you\Downloads\ChipSeeker_xxx.csdl"
```

Use the newest task under Downloads:

```powershell
.\download-latest.ps1
```

Choose a folder or browser:

```powershell
.\.venv\Scripts\python.exe .\downloader.py task.csdl --output D:\Papers --browser msedge
```

## Output

- Valid PDF files
- `download_report.json`
- `failed_downloads.md` when some papers need manual handling

The downloader does not bypass publisher access controls. It uses the user's own network access and the cookies stored only in its local `user_profile` directory.
