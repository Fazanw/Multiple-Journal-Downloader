import asyncio
import threading
import os
import csv
import socket
import webbrowser
import datetime
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.parser import parse_file
from core.downloader import UnpaywallDownloader
from core.updater import check_for_updates, APP_VERSION

# Design Tokens
COLOR_PRIMARY = "#374F6B"
COLOR_ACCENT = "#FFD700"  # Yellow
COLOR_BG = "#F8F9FA"
COLOR_SURFACE = "#FFFFFF"

class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"Multi Reference Downloader v{APP_VERSION}")
        self.geometry("1100x700")
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BG)
        
        # Set Application Icon using high-res PNG for crisp titlebar rendering
        import tkinter as tk
        if os.path.exists("icon.png"):
            try:
                img = tk.PhotoImage(file="icon.png")
                self.iconphoto(False, img)
            except Exception as e:
                print(f"Could not load iconphoto: {e}")
        elif os.path.exists("icon.ico"):
            try:
                self.iconbitmap("icon.ico")
            except Exception as e:
                print(f"Could not load iconbitmap: {e}")
        
        # State
        self.references = []
        self.downloader = UnpaywallDownloader()
        
        # Pagination state
        self.current_page = 0
        self.items_per_page = 15
        
        # Progress state
        self.total_items = 0
        self.processed_items = 0
        self.is_downloading = False
        
        # Throttle UI updates queue
        self._pending_updates = []
        self._update_job = None
        
        self._build_ui()
        self.bind("<Configure>", self._on_window_resize)
        
        # DevOps: Kick off background update checker
        check_for_updates(self)
        
    def _on_window_resize(self, event):
        if event.widget == self:
            try:
                # Windows maximized state is 'zoomed'
                new_limit = 20 if self.state() == "zoomed" else 15
                
                if self.items_per_page != new_limit:
                    self.items_per_page = new_limit
                    if self.references:
                        total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
                        if self.current_page >= total_pages:
                            self.current_page = total_pages - 1
                        self.refresh_table()
            except Exception:
                pass
        
    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_PRIMARY)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Multi Reference\nDownloader", font=ctk.CTkFont(size=18, weight="bold"), text_color="white")
        self.logo_label.pack(pady=30, padx=20)
        
        self.import_btn = ctk.CTkButton(self.sidebar, text="Import Files...", fg_color="transparent", border_width=1, 
                                        text_color="white", hover_color=COLOR_ACCENT, command=self.import_ris)
        self.import_btn.pack(pady=(10, 5), padx=20, fill="x")
        
        self.import_help = ctk.CTkLabel(self.sidebar, text="Supports: .ris, .bib, .csv,\n.json, .xml, .txt", font=ctk.CTkFont(size=10), text_color="#A0B2C6")
        self.import_help.pack(pady=(0, 10), padx=10)
        
        # Activity Log / History
        self.history_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.history_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.history_title = ctk.CTkLabel(self.history_frame, text="Activity Feed", font=ctk.CTkFont(size=14, weight="bold"), text_color="white")
        self.history_title.pack(anchor="w", pady=(0, 10))
        
        self.history_feed = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_feed.pack(fill="both", expand=True)
        
        self.history_empty = ctk.CTkLabel(self.history_feed, text="No recent activity.", text_color="#A0B2C6", font=ctk.CTkFont(slant="italic"))
        self.history_empty.pack(pady=20)
        
        # Watermark Card
        try:
            gh_icon = ctk.CTkImage(light_image=Image.open("github_icon.png"), size=(20, 20))
            self.watermark_card = ctk.CTkButton(
                self.sidebar, 
                image=gh_icon, 
                text=" github.com/fazanw", 
                fg_color="#F8F9FA", 
                text_color="black",
                hover_color="#E2E6EA",
                corner_radius=8,
                height=40,
                command=lambda: webbrowser.open("https://github.com/fazanw")
            )
            self.watermark_card.pack(side="bottom", pady=20, padx=20, fill="x")
        except Exception as e:
            print(f"Could not load github icon: {e}")
            self.watermark_label = ctk.CTkLabel(self.sidebar, text="github.com/fazanw", font=ctk.CTkFont(size=11, slant="italic"), text_color="#A0B2C6", cursor="hand2")
            self.watermark_label.pack(side="bottom", pady=20)
            self.watermark_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/fazanw"))
        
        # Main Workspace
        self.workspace = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.workspace.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.workspace.grid_rowconfigure(2, weight=1)
        self.workspace.grid_columnconfigure(0, weight=1)
        
        self.header = ctk.CTkLabel(self.workspace, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"), text_color="black")
        self.header.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Pagination Controls
        self.pagination_frame = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.pagination_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.prev_btn = ctk.CTkButton(self.pagination_frame, text="< Prev", width=60, command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left", padx=(0, 10))
        
        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Page 1 of 1", text_color="black")
        self.page_label.pack(side="left")
        
        self.next_btn = ctk.CTkButton(self.pagination_frame, text="Next >", width=60, command=self.next_page, state="disabled")
        self.next_btn.pack(side="left", padx=(10, 0))
        
        self.total_label = ctk.CTkLabel(self.pagination_frame, text="Total references: 0", text_color="gray")
        self.total_label.pack(side="right")
        
        # Data Table (Scrollable Frame)
        self.table_frame = ctk.CTkScrollableFrame(self.workspace, fg_color=COLOR_SURFACE)
        self.table_frame.grid(row=2, column=0, sticky="nsew")
        
        # Empty State Label
        self.empty_label = ctk.CTkLabel(self.table_frame, text="No references loaded.\nClick 'Import Files...' to begin.", text_color="gray")
        self.empty_label.pack(pady=100)
        
        # Action Bar (Bottom)
        self.action_frame = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        
        # Progress components
        self.progress_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.progress_frame.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0 / 0 Completed", text_color="black")
        self.progress_label.pack(anchor="w")
        
        # Buttons
        self.cancel_btn = ctk.CTkButton(self.action_frame, text="Cancel", fg_color="#D9534F", hover_color="#C9302C",
                                        text_color="white", command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side="right", padx=(10, 0))
        
        self.start_btn = ctk.CTkButton(self.action_frame, text="Start Batch Download", fg_color=COLOR_PRIMARY, 
                                       text_color="white", command=self.start_download)
        self.start_btn.pack(side="right")
        
    def import_ris(self):
        filetypes = [
            ("All Supported Formats", "*.ris;*.bib;*.csv;*.txt;*.xml;*.json"),
            ("RIS Files", "*.ris"),
            ("BibTeX Files", "*.bib"),
            ("Spreadsheets", "*.csv"),
            ("JSON Data", "*.json"),
            ("Raw Text / XML", "*.txt;*.xml")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.import_btn.configure(state="disabled", text="Parsing...")
            self.empty_label.configure(text="Parsing massive file, please wait...")
            if not self.empty_label.winfo_ismapped():
                self.empty_label.pack(pady=100)
            
            # Offload heavy parsing to a background thread to prevent UI freezing
            threading.Thread(target=self._threaded_parse, args=(filepath,), daemon=True).start()
            
    def _threaded_parse(self, filepath):
        try:
            raw_refs = parse_file(filepath)
            
            # Deduplicate references to ensure exactly 1 file per unique paper
            seen = set()
            self.references = []
            for ref in raw_refs:
                key = ref.get("doi")
                if not key:
                    # Fallback to title if no DOI exists
                    key = ref.get("title", "").strip().lower()
                    
                if key not in seen:
                    seen.add(key)
                    self.references.append(ref)
                    
            self.after(0, self._on_parse_complete)
            self.after(0, lambda: self._log_activity(f"Imported {len(self.references)} papers from {os.path.basename(filepath)}"))
        except Exception as e:
            print(f"Error parsing file: {e}")
            self.after(0, lambda: self._on_parse_error(str(e)))

    def _on_parse_error(self, error_msg):
        self.import_btn.configure(state="normal", text="Import Files...")
        self.empty_label.configure(text=f"Error parsing file:\n{error_msg}")
        messagebox.showerror("Parse Error", f"Failed to parse file: {error_msg}")

    def _on_parse_complete(self):
        self.import_btn.configure(state="normal", text="Import Files...")
        self.total_items = len(self.references)
        self.current_page = 0
        self.total_label.configure(text=f"Total references: {self.total_items}")
        
        if self.empty_label.winfo_exists():
            self.empty_label.pack_forget()
            
        self.refresh_table()
            
    def refresh_table(self):
        # Clear existing widgets except empty label
        for widget in self.table_frame.winfo_children():
            if widget != self.empty_label:
                widget.destroy()
            
        if not self.references:
            self.page_label.configure(text="Page 1 of 1")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            if not self.empty_label.winfo_ismapped():
                self.empty_label.configure(text="No references loaded.\nClick 'Import Files...' to begin.")
                self.empty_label.pack(pady=100)
            return
            
        if self.empty_label.winfo_ismapped():
            self.empty_label.pack_forget()
            
        # Calculate pagination
        total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        self.page_label.configure(text=f"Page {self.current_page + 1} of {total_pages}")
        
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
        
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, self.total_items)
        
        page_refs = self.references[start_idx:end_idx]
        
        for ref in page_refs:
            title = ref.get("title", "Unknown Title")
            doi = ref.get("doi", "No DOI")
            status = ref.get("status", "Pending")
            
            row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=title[:60] + "...", text_color="black").pack(side="left", padx=10)
            
            status_label = ctk.CTkLabel(row, text=status, text_color="blue")
            status_label.pack(side="right", padx=10)
            ref["status_label"] = status_label
            
            # Apply color if already processed
            self._apply_status_color(status_label, status)
            
            ctk.CTkLabel(row, text=doi, text_color="gray").pack(side="right", padx=10)
            
    def next_page(self):
        total_pages = (self.total_items + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_table()
            
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()

    def _apply_status_color(self, label, status):
        if status == "Downloaded":
            label.configure(text_color="green")
        elif "Manual Access Required" in status or "Failed" in status or "No DOI" in status:
            label.configure(text_color="red")
        else:
            label.configure(text_color="blue")

    def _queue_status_update(self, ref):
        # Debounce / Throttle UI updates to prevent Tkinter freezing from massive async floods
        self._pending_updates.append(ref)
        if self._update_job is None:
            self._update_job = self.after(100, self._flush_status_updates)
            
    def _flush_status_updates(self):
        self._update_job = None
        for ref in self._pending_updates:
            self.processed_items += 1
            # Update UI if widget is currently visible on this page
            if "status_label" in ref and ref["status_label"].winfo_exists():
                status = ref.get("status", "")
                ref["status_label"].configure(text=status)
                self._apply_status_color(ref["status_label"], status)
                
        # Batch update the progress bar once for the whole group
        progress_val = self.processed_items / self.total_items if self.total_items > 0 else 0
        self.progress_bar.set(progress_val)
        self.progress_label.configure(text=f"{self.processed_items} / {self.total_items} Completed")
        self._pending_updates.clear()

    def _log_activity(self, msg):
        if self.history_empty.winfo_ismapped():
            self.history_empty.pack_forget()
            
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Create a modern card for the activity
        card = ctk.CTkFrame(self.history_feed, fg_color="#2A3C52", corner_radius=6)
        card.pack(fill="x", pady=(0, 10), padx=2)
        
        time_lbl = ctk.CTkLabel(card, text=timestamp, font=ctk.CTkFont(size=10, weight="bold"), text_color="#A0B2C6")
        time_lbl.pack(anchor="w", padx=10, pady=(6, 0))
        
        # Use wraplength to ensure long messages wrap neatly inside the sidebar
        msg_lbl = ctk.CTkLabel(card, text=msg, font=ctk.CTkFont(size=11), text_color="white", justify="left", wraplength=130)
        msg_lbl.pack(anchor="w", padx=10, pady=(2, 10))
        
        # Auto-scroll to bottom by scrolling the canvas
        self.after(50, lambda: self.history_feed._parent_canvas.yview_moveto(1.0))

    def _check_internet(self):
        """Pre-flight check to see if the computer is online"""
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True
        except OSError:
            pass
        return False
        
    def start_download(self):
        if not self.references:
            messagebox.showinfo("Empty", "Please import a file first.")
            return
            
        if not self._check_internet():
            messagebox.showerror("Network Error", "No internet connection detected. Please connect to the internet and try again.")
            return
            
        out_dir = filedialog.askdirectory(title="Select Download Directory")
        if not out_dir:
            return
            
        self.is_downloading = True
        self.start_btn.configure(state="disabled", text="Downloading...")
        self.cancel_btn.configure(state="normal")
        self.import_btn.configure(state="disabled")
        
        self.processed_items = 0
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"0 / {self.total_items} Completed")
        
        # Generic email bypass (Unpaywall is free)
        self.downloader.email = "anonymous_downloader@example.com"
        
        threading.Thread(target=self._run_async_download, args=(out_dir,), daemon=True).start()
        
    def cancel_download(self):
        if self.is_downloading:
            self.downloader.cancel_event.set()
            self.cancel_btn.configure(state="disabled", text="Cancelling...")
        
    def _run_async_download(self, out_dir):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        def safe_update(ref):
            self.after(0, lambda r=ref: self._queue_status_update(r))
            
        loop.run_until_complete(self.downloader.batch_download(self.references, out_dir, callback=safe_update))
        
        self.after(0, lambda: self._on_download_complete(out_dir))
        
    def _on_download_complete(self, out_dir):
        # Flush any remaining UI updates immediately
        if self._update_job:
            self.after_cancel(self._update_job)
            self._flush_status_updates()
            
        self.is_downloading = False
        self.start_btn.configure(state="normal", text="Start Batch Download")
        self.cancel_btn.configure(state="disabled", text="Cancel")
        self.import_btn.configure(state="normal")
        
        downloaded = sum(1 for r in self.references if r.get("status") == "Downloaded")
        failed_refs = [r for r in self.references if r.get("status") != "Downloaded" and r.get("doi")]
        
        # Export CSV report
        csv_path = os.path.join(out_dir, "failed_downloads.csv")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "DOI", "Status"])
                for r in failed_refs:
                    writer.writerow([r.get("title", ""), r.get("doi", ""), r.get("status", "")])
        except Exception as e:
            print(f"Failed to write CSV: {e}")
            
        msg = (f"Batch processing completed!\n\n"
               f"Successfully Downloaded: {downloaded}\n"
               f"Requires Manual Access/Failed: {len(failed_refs)}\n\n"
               f"A summary report (failed_downloads.csv) has been saved to your download directory.")
               
        if self.downloader.cancel_event.is_set():
            msg = "Download Cancelled.\n\n" + msg
            self._log_activity("Download batch cancelled by user.")
        else:
            self._log_activity(f"Batch complete. Success: {downloaded}, Failed: {len(failed_refs)}")
            
        messagebox.showinfo("Summary Report", msg)

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
