#!/usr/bin/env python3
"""
Smart Funding Advisor - Server Manager GUI
Simple GUI to start, stop, and restart backend and frontend servers
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import signal
import sys
from pathlib import Path
import threading
import time

class ServerManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Funding Advisor - Server Manager")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Process tracking
        self.backend_process = None
        self.frontend_process = None
        
        # Get project directory
        self.project_dir = Path(__file__).parent.absolute()
        self.backend_dir = self.project_dir / "backend"
        self.frontend_dir = self.project_dir / "frontend"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#2563eb', pady=15)
        title_frame.pack(fill='x')
        
        title_label = tk.Label(
            title_frame,
            text="🚀 Smart Funding Advisor Server Manager",
            font=('Arial', 18, 'bold'),
            bg='#2563eb',
            fg='white'
        )
        title_label.pack()
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg='#f0f0f0', padx=20, pady=20)
        content_frame.pack(fill='both', expand=True)
        
        # Backend Server Section
        backend_frame = tk.LabelFrame(
            content_frame,
            text="Backend Server (Port 8000)",
            font=('Arial', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        backend_frame.pack(fill='x', pady=(0, 15))
        
        self.backend_status = tk.Label(
            backend_frame,
            text="● Stopped",
            font=('Arial', 10),
            bg='white',
            fg='red'
        )
        self.backend_status.pack(anchor='w', pady=(0, 10))
        
        backend_buttons = tk.Frame(backend_frame, bg='white')
        backend_buttons.pack(fill='x')
        
        tk.Button(
            backend_buttons,
            text="▶ Start",
            command=self.start_backend,
            bg='#10b981',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            backend_buttons,
            text="■ Stop",
            command=self.stop_backend,
            bg='#ef4444',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            backend_buttons,
            text="↻ Restart",
            command=self.restart_backend,
            bg='#f59e0b',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left')
        
        # Frontend Server Section
        frontend_frame = tk.LabelFrame(
            content_frame,
            text="Frontend Server (Port 3000)",
            font=('Arial', 12, 'bold'),
            bg='white',
            padx=15,
            pady=15
        )
        frontend_frame.pack(fill='x', pady=(0, 15))
        
        self.frontend_status = tk.Label(
            frontend_frame,
            text="● Stopped",
            font=('Arial', 10),
            bg='white',
            fg='red'
        )
        self.frontend_status.pack(anchor='w', pady=(0, 10))
        
        frontend_buttons = tk.Frame(frontend_frame, bg='white')
        frontend_buttons.pack(fill='x')
        
        tk.Button(
            frontend_buttons,
            text="▶ Start",
            command=self.start_frontend,
            bg='#10b981',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            frontend_buttons,
            text="■ Stop",
            command=self.stop_frontend,
            bg='#ef4444',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            frontend_buttons,
            text="↻ Restart",
            command=self.restart_frontend,
            bg='#f59e0b',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=5,
            cursor='hand2'
        ).pack(side='left')
        
        # Quick Actions
        quick_frame = tk.Frame(content_frame, bg='#f0f0f0')
        quick_frame.pack(fill='x', pady=(0, 15))
        
        tk.Button(
            quick_frame,
            text="🚀 Start All Servers",
            command=self.start_all,
            bg='#2563eb',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=30,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            quick_frame,
            text="⏹ Stop All Servers",
            command=self.stop_all,
            bg='#6b7280',
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=30,
            pady=8,
            cursor='hand2'
        ).pack(side='left')
        
        # Console Output
        console_frame = tk.LabelFrame(
            content_frame,
            text="Console Output",
            font=('Arial', 12, 'bold'),
            bg='white',
            padx=10,
            pady=10
        )
        console_frame.pack(fill='both', expand=True)
        
        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=10,
            bg='#1e293b',
            fg='#10b981',
            font=('Courier', 9),
            insertbackground='white'
        )
        self.console.pack(fill='both', expand=True)
        
        # Status Bar
        status_bar = tk.Label(
            self.root,
            text=f"Project: {self.project_dir}",
            bg='#374151',
            fg='white',
            anchor='w',
            padx=10,
            pady=5,
            font=('Arial', 9)
        )
        status_bar.pack(side='bottom', fill='x')
        
        self.log("Server Manager initialized")
        self.log(f"Backend: {self.backend_dir}")
        self.log(f"Frontend: {self.frontend_dir}")
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        
    def start_backend(self):
        if self.backend_process and self.backend_process.poll() is None:
            self.log("⚠ Backend is already running")
            return
            
        self.log("Starting backend server...")
        try:
            self.backend_process = subprocess.Popen(
                ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.backend_status.config(text="● Running", fg='green')
            self.log("✓ Backend server started on http://localhost:8000")
            
            # Monitor output in background
            threading.Thread(target=self.monitor_backend, daemon=True).start()
            
        except Exception as e:
            self.log(f"✗ Error starting backend: {e}")
            
    def stop_backend(self):
        if not self.backend_process or self.backend_process.poll() is not None:
            self.log("⚠ Backend is not running")
            return
            
        self.log("Stopping backend server...")
        try:
            self.backend_process.terminate()
            self.backend_process.wait(timeout=5)
            self.backend_status.config(text="● Stopped", fg='red')
            self.log("✓ Backend server stopped")
        except subprocess.TimeoutExpired:
            self.backend_process.kill()
            self.log("✓ Backend server killed (forced)")
        except Exception as e:
            self.log(f"✗ Error stopping backend: {e}")
            
    def restart_backend(self):
        self.log("Restarting backend server...")
        self.stop_backend()
        time.sleep(1)
        self.start_backend()
        
    def start_frontend(self):
        if self.frontend_process and self.frontend_process.poll() is None:
            self.log("⚠ Frontend is already running")
            return
            
        self.log("Starting frontend server...")
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd=str(self.frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.frontend_status.config(text="● Running", fg='green')
            self.log("✓ Frontend server started on http://localhost:3000")
            
            # Monitor output in background
            threading.Thread(target=self.monitor_frontend, daemon=True).start()
            
        except Exception as e:
            self.log(f"✗ Error starting frontend: {e}")
            
    def stop_frontend(self):
        if not self.frontend_process or self.frontend_process.poll() is not None:
            self.log("⚠ Frontend is not running")
            return
            
        self.log("Stopping frontend server...")
        try:
            self.frontend_process.terminate()
            self.frontend_process.wait(timeout=5)
            self.frontend_status.config(text="● Stopped", fg='red')
            self.log("✓ Frontend server stopped")
        except subprocess.TimeoutExpired:
            self.frontend_process.kill()
            self.log("✓ Frontend server killed (forced)")
        except Exception as e:
            self.log(f"✗ Error stopping frontend: {e}")
            
    def restart_frontend(self):
        self.log("Restarting frontend server...")
        self.stop_frontend()
        time.sleep(1)
        self.start_frontend()
        
    def start_all(self):
        self.log("Starting all servers...")
        self.start_backend()
        time.sleep(2)
        self.start_frontend()
        
    def stop_all(self):
        self.log("Stopping all servers...")
        self.stop_backend()
        self.stop_frontend()
        
    def monitor_backend(self):
        """Monitor backend output"""
        try:
            for line in self.backend_process.stdout:
                if "Application startup complete" in line:
                    self.log("✓ Backend ready")
                elif "ERROR" in line or "Error" in line:
                    self.log(f"Backend error: {line.strip()}")
        except:
            pass
            
    def monitor_frontend(self):
        """Monitor frontend output"""
        try:
            for line in self.frontend_process.stdout:
                if "webpack compiled" in line.lower():
                    self.log("✓ Frontend ready")
                elif "error" in line.lower() and "ERROR in" in line:
                    self.log(f"Frontend error detected")
        except:
            pass
            
    def on_closing(self):
        """Clean up when closing"""
        self.log("Shutting down server manager...")
        self.stop_all()
        time.sleep(1)
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ServerManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
