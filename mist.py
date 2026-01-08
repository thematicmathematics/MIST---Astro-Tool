import sys
import os
import numpy as np
import csv  
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.interpolate import interp1d
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QFrame, 
                             QGraphicsDropShadowEffect, QProgressBar, 
                             QFileDialog, QDoubleSpinBox, QSpinBox, QTextEdit, QMessageBox, QSplashScreen)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QIcon

def resource_path(relative_path):
    try:        
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 1. CONFIG & STYLES
COLOR_BG = "#121212"
COLOR_PANEL = "#1E2224"
COLOR_BORDER = "#2A3035"
COLOR_TEXT_PRI = "#E0F7FA"
COLOR_TEXT_SEC = "#90A4AE"
ACCENT_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00E5FF, stop:1 #0091EA)" 
ACCENT_GLOW = "#00E5FF"
FONT_FAMILY = "'Segoe UI', 'Verdana', sans-serif"
FONT_HUD = "'Consolas', 'Courier New', monospace"
STYLE_SHEET = f"""
    QMainWindow {{ background-color: {COLOR_BG}; }}
    QLabel {{ color: {COLOR_TEXT_SEC}; font-family: {FONT_FAMILY}; font-size: 11px; font-weight: bold; letter-spacing: 1px; }}
    QLabel[class="PanelHeader"] {{ color: {ACCENT_GLOW}; font-size: 10px; letter-spacing: 2px; margin-bottom: 5px; }}
    QDoubleSpinBox, QSpinBox {{
        background-color: #101518; color: {COLOR_TEXT_PRI};
        border: 1px solid #37474F; border-radius: 4px; padding: 5px;
        font-family: {FONT_HUD}; font-weight: bold;
    }}
    QDoubleSpinBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT_GLOW}; }}
    QProgressBar {{ border: none; border-radius: 3px; background-color: #101518; text-align: center; color: transparent; }}
    QProgressBar::chunk {{ background: {ACCENT_GRADIENT}; border-radius: 3px; }}
    QTextEdit {{
        background-color: #0A0D0E; color: #00E676;
        border: 1px solid #263238; border-radius: 4px;
        font-family: {FONT_HUD}; font-size: 10px;
    }}
"""
CYAN_BTN_STYLE = """
    QPushButton {
        background-color: #00BCD4;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00E5FF, stop:1 #0091EA);
        color: #000000;
        border: 1px solid #00B0FF;
        border-bottom: 4px solid #006064;
        border-radius: 6px;
        font-family: 'Segoe UI Black', 'Arial Black', sans-serif;
        font-size: 14px;
        font-weight: 900;
        letter-spacing: 1px;
        padding: 8px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #40C4FF, stop:1 #00B0FF);
        border-bottom: 4px solid #00838F;
    }
    QPushButton:pressed {
        border-bottom: 0px solid #006064;
        border-top: 2px solid #003032;
        padding-top: 10px;
        padding-bottom: 4px;
    }
    QPushButton:disabled {
        background: #263238; color: #546E7A; border: 1px solid #37474F; border-bottom: 4px solid #202020;
    }
"""
FILE_BTN_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_PANEL}; color: {COLOR_TEXT_PRI};
        border: 1px dashed #546E7A; border-radius: 6px;
        font-family: {FONT_FAMILY}; font-size: 11px; font-weight: bold;
    }}
    QPushButton:hover {{ border: 1px dashed {ACCENT_GLOW}; color: {ACCENT_GLOW}; background-color: #263238; }}
"""
SUCCESS_BTN_STYLE = """
    QPushButton {
        background-color: #263238; color: #00E676;
        border: 1px solid #00E676; border-radius: 6px;
        font-weight: bold; font-size: 12px;
    }
    QPushButton:hover { background-color: #00E676; color: #000; }
"""
# 2. CUSTOM UI COMPONENTS 
class SectionFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 12px;")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        c = QColor("#000000"); c.setAlphaF(0.5)
        shadow.setColor(c); shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

# 3. CALCULATION ENGINE
class AstroEngine:
    @staticmethod
    def analyze_single_event(x, y):
        x_offset = x[0]; x_c = x - x_offset
        # Parabolic
        try:
            coeffs, cov = np.polyfit(x_c, y, 2, cov=True)
            a, b, c = coeffs
            t_par = (-b / (2 * a)) + x_offset
            var_a, var_b = cov[0,0], cov[1,1]; cov_ab = cov[0,1]
            sigma_par = np.sqrt(abs((var_b/(4*a**2)) + ((b**2*var_a)/(4*a**4)) - ((2*b*cov_ab)/(4*a**3))))
            fx = np.linspace(min(x), max(x), 50); fy = a * (fx - x_offset)**2 + b * (fx - x_offset) + c
        except: t_par, sigma_par, fx, fy = np.nan, 9.999, [], []
        # KvW
        try:
            f_interp = interp1d(x_c, y, kind='linear', fill_value="extrapolate")
            center = np.mean(x_c); search = (x_c[-1] - x_c[0]) / 3
            t_trials = np.linspace(center - search, center + search, 50)
            s_sq = []
            for t in t_trials:
                x_ref = 2 * t - x_c
                mask = (x_ref >= x_c[0]) & (x_ref <= x_c[-1])
                if np.sum(mask) < 3: s_sq.append(np.inf)
                else: s_sq.append(np.sum((y[mask] - f_interp(x_ref[mask]))**2))
            s_sq = np.array(s_sq); valid = np.isfinite(s_sq)
            if np.sum(valid) > 4:
                t_c, s_c = t_trials[valid], s_sq[valid]
                b_idx = np.argmin(s_c); sl = slice(max(0, b_idx-5), min(len(s_c), b_idx+5))
                A, B, C = np.polyfit(t_c[sl], s_c[sl], 2)
                if A > 0:
                    t_kvw = (-B / (2 * A)) + x_offset
                    sigma_kvw = np.sqrt(2 * abs(C - (B**2)/(4*A)) / (A * (len(x)-2)))
                else: t_kvw, sigma_kvw = np.nan, 9.999
            else: t_kvw, sigma_kvw = np.nan, 9.999
        except: t_kvw, sigma_kvw = np.nan, 9.999
        return t_kvw, sigma_kvw, t_par, sigma_par, fx, fy

# 4. WORKER 
class AnalysisWorker(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)    
    def __init__(self, params):
        super().__init__()
        self.p = params
        self.engine = AstroEngine()

    def run(self):
        try:
            fpath = self.p['filepath']
            folder = os.path.dirname(fpath)
            base = os.path.basename(fpath).split('.')[0]
            out_dir = os.path.join(folder, f"{base}_Detailed_Analysis")
            os.makedirs(out_dir, exist_ok=True)
            eps_dir = os.path.join(out_dir, "EPS_Figures")
            os.makedirs(eps_dir, exist_ok=True)            
            self.log.emit(f"SESSION START: {base}", "#FFFFFF")            
            try: data = np.loadtxt(fpath)
            except: data = np.loadtxt(fpath, delimiter=',')
            bjd, mag, phase = data[:,0], data[:,1], data[:,2]            
            self.log.emit(f"DATA LOADED: {len(bjd)} ROWS", "#00E676")
            self.progress.emit(10)
            
            header_line = f"{'ID':<15} | {'KvW Time':<15} +/- {'Err':<10} | {'Par Time':<15} +/- {'Err':<10} | {'Status'}"
            separator = "-" * len(header_line)
            results = [f"ANALYSIS REPORT: {base}", f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "-"*50, header_line, separator]            
            ml_data = []
            ranges = [
                (self.p['p_min'], self.p['p_max'], "Primary"),
                (self.p['s_min'], self.p['s_max'], "Secondary")
            ]
            
            total_steps = 2
            current_step = 0
            
            for p_min, p_max, lbl in ranges:
                self.log.emit(f"SCANNING {lbl.upper()}...", "#29B6F6")
                mask = (phase >= p_min) & (phase <= p_max)
                x_f, y_f = bjd[mask], mag[mask]
                
                if len(x_f) > 0:
                    sort = np.argsort(x_f)
                    x_s, y_s = x_f[sort], y_f[sort]
                    splits = np.where(np.diff(x_s) > 0.3)[0] + 1
                    cx, cy = np.split(x_s, splits), np.split(y_s, splits)
                    
                    valid_cnt = 0
                    for x_chunk, y_chunk in zip(cx, cy):
                        if len(x_chunk) < self.p['min_points']: continue
                        valid_cnt += 1
                        min_id = f"{lbl}_{valid_cnt}"                        
                        t_kvw, e_kvw, t_par, e_par, fx, fy = self.engine.analyze_single_event(x_chunk, y_chunk)
                        
                        if not np.isnan(t_par):
                            mc_kvw, mc_par = [], []
                            x_off = x_chunk[0]
                            c_poly = np.polyfit(x_chunk - x_off, y_chunk, 2)
                            resid = y_chunk - np.poly1d(c_poly)(x_chunk - x_off)
                            noise = np.std(resid)
                            
                            for _ in range(self.p['mc_iter']):
                                y_n = y_chunk + np.random.normal(0, noise, len(y_chunk))
                                mk, _, mp, _, _, _ = self.engine.analyze_single_event(x_chunk, y_n)
                                if not np.isnan(mk): mc_kvw.append(mk)
                                if not np.isnan(mp): mc_par.append(mp)                            
                            fe_kvw = np.std(mc_kvw) if mc_kvw else e_kvw
                            fe_par = np.std(mc_par) if mc_par else e_par
                            status = "CHECK" if abs(t_kvw - t_par) > self.p['threshold'] else "OK"                            
                            results.append(f"{min_id:<15} | {t_kvw:.5f} +/- {fe_kvw:.5f} | {t_par:.5f} +/- {fe_par:.5f} | {status}")
                            ml_data.append({'ID': min_id, 'KvW': t_kvw, 'Par': t_par, 'Status': status})
                            
                            # DRAW GRAPH
                            self.plot(x_chunk, y_chunk, fx, fy, t_kvw, min_id, resid, out_dir, eps_dir)
                            color_log = "#FF5555" if status == "CHECK" else "#90A4AE"
                            self.log.emit(f"-> {min_id} ({status})", color_log)                            
                current_step += 1
                self.progress.emit(10 + int((current_step/total_steps)*80))

            # REPORT.TXT 
            with open(os.path.join(out_dir, "Minima_Report.txt"), "w") as f: f.write("\n".join(results))
            
            # CSV 
            if ml_data:
                csv_path = os.path.join(out_dir, "ML_Data.csv")
                try:
                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['ID', 'KvW', 'Par', 'Status'])
                        writer.writeheader()
                        writer.writerows(ml_data)
                except Exception as e:
                    self.log.emit(f"CSV ERROR: {str(e)}", "#FF5555")            
            self.progress.emit(100)
            self.log.emit("ANALYSIS COMPLETED SUCCESSFULLY", "#00E676")
            self.finished.emit(out_dir)
        except Exception as e:
            self.log.emit(f"CRITICAL ERROR: {str(e)}", "#FF0000")
            self.finished.emit("ERROR")

    def plot(self, x, y, fx, fy, tm, title, res, folder, eps_folder):
        plt.style.use('default') 
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        
        # LIGHT CURVE & FIT
        ax1.plot(x, y, 'ko', alpha=0.7, label='Obs') 
        if len(fx)>0: ax1.plot(fx, fy, 'r-', lw=2, label='Fit') 
        if not np.isnan(tm): ax1.axvline(tm, color='blue', ls='--', alpha=0.5)        
        ax1.set_title(f"{title} (Minima Analysis)", color='black', fontsize=12)
        ax1.set_ylabel("Magnitude / Flux")
        ax1.invert_yaxis()
        ax1.legend()
        ax1.grid(True, linestyle=':', alpha=0.3)
        
        # Residuals 
        ax2.scatter(x, res, c='black', s=10)
        ax2.axhline(0, c='red', ls='--') 
        ax2.set_ylabel("Res.")
        ax2.set_xlabel("BJD (Time)")
        ax2.grid(True, linestyle=':', alpha=0.3)        
        plt.tight_layout()
        plt.savefig(os.path.join(folder, f"{title}.png"), dpi=150) 
        plt.savefig(os.path.join(eps_folder, f"{title}.eps"), format='eps')
        plt.close(fig)

# 5. MAIN WINDOW (GUI) 
class AstroHunterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M.I.S.T")               
        icon_path = resource_path("MIST_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))            
        self.setFixedSize(500, 780)
        self.filepath = None
        self.worker = None
        self.thread = None
        self.last_output_dir = None
        container = QWidget(); self.setCentralWidget(container)
        main_layout = QVBoxLayout(container); main_layout.setSpacing(15); main_layout.setContentsMargins(25, 25, 25, 25)

        # 6. HEADER
        lbl_title = QLabel("M.I.S.T"); lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #FFF; letter-spacing: 3px; margin-bottom: 5px;")
        lbl_sub = QLabel("Minima Identification Search Tool"); lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {ACCENT_GLOW}; font-size: 10px; font-weight: bold; letter-spacing: 5px;")
        main_layout.addWidget(lbl_title); main_layout.addWidget(lbl_sub)

        # 7. DATA SOURCE
        panel_data = SectionFrame()
        pd_layout = QVBoxLayout(panel_data); pd_layout.setContentsMargins(15,15,15,15)
        lbl_d = QLabel("DATA SOURCE"); lbl_d.setProperty("class", "PanelHeader")
        pd_layout.addWidget(lbl_d)        
        self.btn_file = QPushButton("📂  SELECT OBSERVATION FILE")
        self.btn_file.setStyleSheet(FILE_BTN_STYLE)
        self.btn_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_file.setFixedHeight(40)
        self.btn_file.clicked.connect(self.select_file)
        pd_layout.addWidget(self.btn_file)        
        self.lbl_file_status = QLabel("NO FILE SELECTED"); self.lbl_file_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_file_status.setStyleSheet("color: #546E7A; font-size: 10px; margin-top: 5px;")
        pd_layout.addWidget(self.lbl_file_status)
        main_layout.addWidget(panel_data)

        # 8 PARAMETERS
        panel_params = SectionFrame()
        pp_layout = QVBoxLayout(panel_params); pp_layout.setContentsMargins(15,15,15,15)
        
        lbl_p = QLabel("ANALYSIS CONFIGURATION"); lbl_p.setProperty("class", "PanelHeader")
        pp_layout.addWidget(lbl_p)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("PRIMARY PHASE:"))
        self.sp_pmin = self.create_spinner(0.95); row1.addWidget(self.sp_pmin)
        self.sp_pmax = self.create_spinner(1.05); row1.addWidget(self.sp_pmax)
        pp_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("SECONDARY PHASE:"))
        self.sp_smin = self.create_spinner(1.45); row2.addWidget(self.sp_smin)
        self.sp_smax = self.create_spinner(1.55); row2.addWidget(self.sp_smax)
        pp_layout.addLayout(row2)
        
        sep = QFrame(); sep.setFixedHeight(1); sep.setStyleSheet("background-color: #37474F; margin: 5px 0;")
        pp_layout.addWidget(sep)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("MC Iter. "))
        self.sp_mc = QSpinBox(); self.sp_mc.setRange(10, 1000); self.sp_mc.setValue(100); self.sp_mc.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.sp_mc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row3.addWidget(self.sp_mc)
        
        row3.addWidget(QLabel("Min Point"))
        self.sp_pts = QSpinBox(); self.sp_pts.setRange(3, 20); self.sp_pts.setValue(5); self.sp_pts.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.sp_pts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row3.addWidget(self.sp_pts)
        row3.addWidget(QLabel("Threshold"))
        self.sp_threshold = QDoubleSpinBox()
        self.sp_threshold.setRange(0.001, 0.100) 
        self.sp_threshold.setSingleStep(0.001)
        self.sp_threshold.setDecimals(3)
        self.sp_threshold.setValue(0.005) 
        self.sp_threshold.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_threshold.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row3.addWidget(self.sp_threshold)
        pp_layout.addLayout(row3)
        main_layout.addWidget(panel_params)

        # 9. ACTION
        panel_act = SectionFrame()
        pa_layout = QVBoxLayout(panel_act); pa_layout.setContentsMargins(15,15,15,15)        
        self.btn_run = QPushButton("Start Analysis")
        self.btn_run.setStyleSheet(CYAN_BTN_STYLE)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_analysis)
        pa_layout.addWidget(self.btn_run)        
        self.pbar = QProgressBar(); self.pbar.setFixedHeight(6)
        pa_layout.addWidget(self.pbar)        
        self.btn_reset = QPushButton("🔄 RESET SYSTEM")
        self.btn_reset.setStyleSheet(FILE_BTN_STYLE) 
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_ui) 
        pa_layout.addWidget(self.btn_reset)        
        self.btn_open = QPushButton("📂 OPEN OUTPUT FOLDER")
        self.btn_open.setStyleSheet(SUCCESS_BTN_STYLE)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_output_folder)
        self.btn_open.setVisible(False)
        pa_layout.addWidget(self.btn_open)
        main_layout.addWidget(panel_act)

        # 10. LOG
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("SYSTEM READY. WAITING FOR INPUT...")
        main_layout.addWidget(self.log_box)

        # 11. SIGNATURE
        lbl_sig = QLabel('<a href="https://thematicmathematics.com" style="color: #455A64; text-decoration: none;">by thematicmathematics.com</a>')
        lbl_sig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sig.setStyleSheet("font-family: 'Segoe UI'; font-style: italic; font-size: 10px; margin-top: 5px;")            
        lbl_sig.setOpenExternalLinks(True) 
        lbl_sig.setCursor(Qt.CursorShape.PointingHandCursor)        
        main_layout.addWidget(lbl_sig)

    def create_spinner(self, val):
        sp = QDoubleSpinBox()
        sp.setRange(0.0, 3.0); sp.setSingleStep(0.01); sp.setDecimals(3); sp.setValue(val)
        sp.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons) 
        sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return sp

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Observation Data", "", "Data Files (*.txt *.dat *.csv)")
        if path:
            self.filepath = path
            name = os.path.basename(path)
            self.lbl_file_status.setText(f"LINKED: {name}")
            self.lbl_file_status.setStyleSheet(f"color: {ACCENT_GLOW}; font-weight: bold; margin-top: 5px;")
            self.log_to_console(f"FILE SELECTED: {name}", "#90A4AE")
            self.btn_open.setVisible(False)

    def start_analysis(self):
        if not self.filepath:
            QMessageBox.warning(self, "INPUT ERROR", "Please select a data file first.")
            return

        params = {
            'filepath': self.filepath,
            'p_min': self.sp_pmin.value(), 'p_max': self.sp_pmax.value(),
            's_min': self.sp_smin.value(), 's_max': self.sp_smax.value(),
            'mc_iter': self.sp_mc.value(), 'min_points': self.sp_pts.value(),
            'threshold': self.sp_threshold.value()
        }

        self.btn_run.setEnabled(False); self.btn_run.setText("PROCESSING...")
        self.btn_open.setVisible(False)
        self.log_box.clear()
        self.pbar.setValue(0)        
        self.thread = QThread()
        self.worker = AnalysisWorker(params)
        self.worker.moveToThread(self.thread)        
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.log.connect(self.log_to_console)
        self.worker.finished.connect(self.analysis_done)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    def analysis_done(self, result):
        self.btn_run.setEnabled(True); self.btn_run.setText("START ANALYSIS")
        if result != "ERROR":
            self.last_output_dir = result
            self.btn_open.setVisible(True)
            QMessageBox.information(self, "SUCCESS", f"Analysis stored in:\n{result}")
    def open_output_folder(self):
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_output_dir))
    def log_to_console(self, msg, color="#FFFFFF"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"<span style='color:#555'>[{ts}]</span> <span style='color:{color}'>{msg}</span>")
    def reset_ui(self):       
        self.filepath = None        
        self.lbl_file_status.setText("NO FILE SELECTED")
        self.lbl_file_status.setStyleSheet("color: #546E7A; font-size: 10px; margin-top: 5px;")        
        self.log_box.clear()        
        self.pbar.setValue(0)        
        self.btn_open.setVisible(False)        
        self.log_to_console("SYSTEM RESET. READY FOR NEW SESSION.", "#00E5FF")
        self.sp_threshold.setValue(0.005)
if __name__ == "__main__":
    import ctypes    
    try:
        myappid = 'mist.v1.astro.hunter'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)    
    icon_path = resource_path("MIST_icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()     
    if not app_icon.isNull():
        pixmap = app_icon.pixmap(256, 256)
        splash = QSplashScreen(pixmap)
        splash.show()
        splash.showMessage("\n\n\n\n\n\n\n\n\n\nsystem initializing......",
                           Qt.AlignmentFlag.AlignCenter, QColor("#00E5FF"))           
        window = AstroHunterWindow()
        splash.finish(window)
    else:
        window = AstroHunterWindow()
    window.show()
    sys.exit(app.exec())


    