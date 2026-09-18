# Multi Reference Downloader

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![OS](https://img.shields.io/badge/OS-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Multi Reference Downloader** is a high-performance, ultra-lightweight desktop application designed for researchers, academics, and students. It completely automates the process of fetching and downloading Open Access academic papers and journals in bulk. 

Instead of manually searching for hundreds of DOIs one by one, simply drop in your reference file (e.g., from EndNote, Mendeley, Zotero, or a raw spreadsheet), and the application will instantly hunt down and download the legal Open Access PDFs directly to your hard drive.

## 🚀 Key Features

- **8-Layer Fallback Engine:** Maximizes your download success rate by automatically cascading through 8 of the world's largest academic databases (Unpaywall, Crossref, Europe PMC, OpenAlex, Semantic Scholar, Internet Archive Scholar, HAL, and Zenodo).
- **Universal Format Support:** Seamlessly parses `.ris`, `.bib`, `.csv`, `.json`, `.xml`, and even unstructured raw `.txt` files.
- **Ultra-Lightweight & Fast:** Engineered with an asynchronous Python network stack and strict memory governing. It can process 50,000+ references concurrently without freezing your computer or consuming excess RAM.
- **Smart Deduplication:** Automatically detects and skips duplicate DOIs or files that already exist in your destination folder to save bandwidth.
- **Fail-Safe Exports:** Automatically generates a `failed_downloads.csv` report for any papers that are strictly paywalled, allowing you to easily track what requires manual access.
- **Continuous Delivery:** Built-in OTA (Over-The-Air) updater ensures you always have the latest features and bug fixes.

## 💻 System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Memory (RAM):** 512 MB minimum (Extremely memory efficient)
- **Storage:** ~50 MB for the application, plus additional space for downloaded PDFs
- **Network:** Active broadband internet connection required

## 📥 Installation

1. Go to the [Releases](https://github.com/fazanw/Multiple-Journal-Downloader/releases/latest) page.
2. Download the latest `Multi_Reference_Downloader_Setup.exe` installer file.
3. Double-click the installer and follow the on-screen prompts.
4. Launch the application from your Desktop or Start Menu.

*(Note: Because this is a custom-built open-source tool, Windows Defender SmartScreen might display a "Windows protected your PC" warning. Click **More Info** > **Run Anyway** to proceed with the installation.)*

## 📖 How to Use

1. **Export your references:** Export your library from Mendeley, Zotero, EndNote, or simply paste a list of DOIs into a `.txt` file.
2. **Open the App:** Launch **Multi Reference Downloader**.
3. **Import:** Click the `Import Files...` button on the left sidebar and select your file.
4. **Review:** Wait a moment for the parsing engine to extract the DOIs, then review the paginated Dashboard data table.
5. **Download:** Click `Start Batch Download` and select a destination folder on your computer.
6. **Relax:** The app will rapidly and asynchronously download all available Open Access PDFs directly to your chosen folder.

## ⚠️ Disclaimer & Legal

This application strictly downloads **Open Access** papers that have been legally distributed by authors, publishers, or open-science repositories. 
- It **does not** bypass publisher paywalls.
- It **does not** interact with shadow libraries (e.g., Sci-Hub).
- It relies entirely on public APIs. If a paper is strictly paywalled and no legal open-access copy exists anywhere on the internet, the application will skip it and mark it as "Manual Access Required".

## 📝 Changelog & Release Notes

To see the full history of enhancements, bug fixes, and what has been built in each version of the app, please visit the [Releases Page](https://github.com/fazanw/Multiple-Journal-Downloader/releases).

## 👨‍💻 Developer

Built by [Faza](https://www.linkedin.com/in/fazanurw/).
