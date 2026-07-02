import sys, os, subprocess, tifffile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QFileDialog, QGroupBox, QGridLayout,
                             QMessageBox, QCheckBox, QComboBox, QRadioButton, 
                             QButtonGroup, QTabWidget, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class BatchScriptEditor(QDialog):
    """Dialog for creating batch scripts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Script Editor")
        self.setGeometry(200, 200, 900, 600)
        
        # Make it non-modal so main window stays editable
        self.setModal(False)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Paste commands below (one per line). Each will execute in order.")
        layout.addWidget(instructions)
        
        # Text editor for commands
        self.editor = QTextEdit()
        self.editor.setStyleSheet("font-family: monospace;")
        self.editor.setPlaceholderText("Paste your commands here...")
        layout.addWidget(self.editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_current_btn = QPushButton("Copy Current Command")
        copy_current_btn.clicked.connect(self.copy_current_command)
        button_layout.addWidget(copy_current_btn)
        
        button_layout.addStretch()
        
        run_btn = QPushButton("Run Batch Script")
        run_btn.clicked.connect(self.run_batch)
        run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(run_btn)
        
        layout.addLayout(button_layout)
        
        self.parent_window = parent
    
    def copy_current_command(self):
        """Copy the current command from main window"""
        if self.parent_window:
            # Determine which tab is active
            current_tab = self.parent_window.tabs.currentIndex()
            if current_tab == 0:  # Reconstruction tab
                command = self.parent_window.recon_command_text.toPlainText()
            else:  # Reslicing tab
                command = self.parent_window.reslice_command_text.toPlainText()
            
            if command:
                # Append to editor
                current_text = self.editor.toPlainText()
                if current_text and not current_text.endswith('\n'):
                    current_text += '\n'
                self.editor.setPlainText(current_text + command + '\n')
    
    def run_batch(self):
        """Run the batch script"""
        commands = self.editor.toPlainText().strip().split('\n')
        commands = [cmd.strip() for cmd in commands if cmd.strip()]
        
        if not commands:
            QMessageBox.warning(self, "No Commands", "Please add at least one command.")
            return
        
        # Generate and run script
        script_lines = ["import os", ""]
        for cmd in commands:
            script_lines.append(f"os.system('{cmd}')")
        
        script_content = '\n'.join(script_lines)
        
        # Save to temporary file
        temp_script = "temp_batch_script.py"
        
        try:
            with open(temp_script, 'w') as f:
                f.write(script_content)
            
            print("\n" + "="*80)
            print(f"Running batch script with {len(commands)} commands...")
            print("="*80 + "\n")
            
            # Run the script
            subprocess.run(f"python {temp_script}", shell=True)
            
            print("\n" + "="*80)
            print("Batch script completed")
            print("="*80 + "\n")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run batch script:\n{str(e)}")

class CTReconstructionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CT Reconstruction & Reslicing")
        self.setGeometry(100, 100, 900, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Dynamic & Time-lapse CT Reconstruction & Reslicing")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create reconstruction tab
        self.reconstruction_tab = self.create_reconstruction_tab()
        self.tabs.addTab(self.reconstruction_tab, "Reconstruction")
        
        # Create reslicing tab
        self.reslicing_tab = self.create_reslicing_tab()
        self.tabs.addTab(self.reslicing_tab, "Reslicing")
        
    def create_reconstruction_tab(self):
        """Create the reconstruction tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # === PATHS GROUP ===
        paths_group = QGroupBox("Paths")
        paths_layout = QGridLayout()

        # Row 0: Project number
        paths_layout.addWidget(QLabel("Project number:"), 0, 0)
        self.project_edit = QLineEdit()
        self.project_edit.setPlaceholderText("##X#####  e.g. 24G00123")
        self.project_edit.setToolTip(
            "Format: ##X#####\n"
            "  ## = two-digit cycle number\n"
            "  X  = access type:\n"
            "         G = General user\n"
            "         R = Rapid access\n"
            "         M = Maintenance\n"
            "         P = Paid access\n"
            "         E = Education\n"
            "         B = Beam team\n"
            "  ##### = five-digit project number"
        )
        paths_layout.addWidget(self.project_edit, 0, 1)
        self.project_status = QLabel("")
        self.project_status.setStyleSheet("color: grey; font-style: italic;")
        paths_layout.addWidget(self.project_status, 0, 2)
        self.project_edit.textChanged.connect(self.update_paths_from_project)

        # Flats/Darks folder
        paths_layout.addWidget(QLabel("Flats/Darks path:"), 1, 0)
        self.flatsdarks_edit = QLineEdit("")
        paths_layout.addWidget(self.flatsdarks_edit, 1, 1)
        flatsdarks_btn = QPushButton("Browse")
        flatsdarks_btn.clicked.connect(lambda: self.browse_folder(self.flatsdarks_edit))
        paths_layout.addWidget(flatsdarks_btn, 1, 2)
        
        # Tomo folder
        paths_layout.addWidget(QLabel("Tomo path:"), 2, 0)
        self.tomo_edit = QLineEdit("")
        paths_layout.addWidget(self.tomo_edit, 2, 1)
        tomo_btn = QPushButton("Browse")
        tomo_btn.clicked.connect(lambda: self.browse_folder(self.tomo_edit))
        paths_layout.addWidget(tomo_btn, 2, 2)
        
        # Save path
        paths_layout.addWidget(QLabel("Save path:"), 3, 0)
        self.save_edit = QLineEdit("")
        paths_layout.addWidget(self.save_edit, 3, 1)
        save_btn = QPushButton("Browse")
        save_btn.clicked.connect(lambda: self.browse_folder(self.save_edit))
        paths_layout.addWidget(save_btn, 3, 2)
        
        # Temp path
        paths_layout.addWidget(QLabel("Temp path:"), 4, 0)
        self.temp_edit = QLineEdit("")
        paths_layout.addWidget(self.temp_edit, 4, 1)
        temp_btn = QPushButton("Browse")
        temp_btn.clicked.connect(lambda: self.browse_folder(self.temp_edit))
        paths_layout.addWidget(temp_btn, 4, 2)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # === BASIC PARAMETERS GROUP ===
        basic_group = QGroupBox("Basic Parameters")
        basic_layout = QGridLayout()
        
        # CT Mode selection - left justified
        basic_layout.addWidget(QLabel("CT Mode:"), 0, 0)
        
        # Create a horizontal layout for the radio buttons
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        self.mode_button_group = QButtonGroup()
        
        self.dynamic_radio = QRadioButton("Dynamic CT")
        self.dynamic_radio.setChecked(True)
        self.dynamic_radio.toggled.connect(self.update_mode_state)
        self.mode_button_group.addButton(self.dynamic_radio)
        mode_layout.addWidget(self.dynamic_radio)
        
        self.timelapse_radio = QRadioButton("Time-lapse CT")
        self.timelapse_radio.toggled.connect(self.update_mode_state)
        self.mode_button_group.addButton(self.timelapse_radio)
        mode_layout.addWidget(self.timelapse_radio)
        
        # Add stretch to push radio buttons to the left
        mode_layout.addStretch()
        
        # Add the horizontal layout to the grid
        basic_layout.addLayout(mode_layout, 0, 1, 1, 2)
        
        # Row 1: Auto-detected image info (read-only)
        basic_layout.addWidget(QLabel("Projections:"), 1, 0)
        self.info_number = QLineEdit("—")
        self.info_number.setReadOnly(True)
        self.info_number.setStyleSheet("color: grey;")
        basic_layout.addWidget(self.info_number, 1, 1)
        basic_layout.addWidget(QLabel("Width:"), 1, 2)
        self.info_width = QLineEdit("—")
        self.info_width.setReadOnly(True)
        self.info_width.setStyleSheet("color: grey;")
        basic_layout.addWidget(self.info_width, 1, 3)
        basic_layout.addWidget(QLabel("Height:"), 1, 4)
        self.info_height = QLineEdit("—")
        self.info_height.setReadOnly(True)
        self.info_height.setStyleSheet("color: grey;")
        basic_layout.addWidget(self.info_height, 1, 5)

        basic_layout.addWidget(QLabel("Number of projections:"), 2, 0)
        self.number_edit = QLineEdit("500")
        basic_layout.addWidget(self.number_edit, 2, 1)

        # Reduce projections (single row: checkbox + target field inline)
        self.reduce_check = QCheckBox("Reduce projections to:")
        self.reduce_check.setChecked(False)
        self.reduce_check.stateChanged.connect(self.update_reduce_state)
        basic_layout.addWidget(self.reduce_check, 3, 0)
        self.reduce_target = QLineEdit("250")
        basic_layout.addWidget(self.reduce_target, 3, 1)
        self.reduce_label_target = QLabel("(leave unchecked to use all)")
        self.reduce_label_target.setStyleSheet("color: grey;")
        basic_layout.addWidget(self.reduce_label_target, 3, 2, 1, 2)

        basic_layout.addWidget(QLabel("Center of Rotation (CoR):"), 5, 0)
        self.cor_edit = QLineEdit("1000")
        basic_layout.addWidget(self.cor_edit, 5, 1)
        
        # Time series (Dynamic CT only)
        self.timeseries_label = QLabel("Time series (start,stop,step):")
        basic_layout.addWidget(self.timeseries_label, 6, 0)
        self.timeseries_edit = QLineEdit("2000,12000,500")
        basic_layout.addWidget(self.timeseries_edit, 6, 1)
        
        # Timelapse search (Time-lapse CT only)
        self.timelapse_label = QLabel("Timelapse search:")
        basic_layout.addWidget(self.timelapse_label, 7, 0)
        self.timelapse_edit = QLineEdit("0,10000,8")
        basic_layout.addWidget(self.timelapse_edit, 7, 1)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # === ARRAY PARAMETERS GROUP ===
        array_group = QGroupBox("Filters and ROI Parameters")
        array_layout = QGridLayout()
        
        row = 0

        # Bright spot removal
        self.spot_check = QCheckBox("Enable Bright Spot Removal")
        self.spot_check.setChecked(False)
        self.spot_check.stateChanged.connect(self.update_spot_state)
        array_layout.addWidget(self.spot_check, row, 0, 1, 2)
        row += 1

        self.spot_label_thresh = QLabel("  Threshold:")
        array_layout.addWidget(self.spot_label_thresh, row, 0)
        self.spot_thresh = QLineEdit("2000")
        array_layout.addWidget(self.spot_thresh, row, 1)
        self.spot_label_sigma = QLabel("Gaussian sigma:")
        array_layout.addWidget(self.spot_label_sigma, row, 2)
        self.spot_sigma = QLineEdit("5")
        array_layout.addWidget(self.spot_sigma, row, 3)
        row += 1

        # Phase params
        self.phase_check = QCheckBox("Enable Phase Retrieval")
        self.phase_check.setChecked(False)
        self.phase_check.stateChanged.connect(self.update_phase_state)
        array_layout.addWidget(self.phase_check, row, 0, 1, 2)
        row += 1
        
        self.phase_label_energy = QLabel("  Energy (keV):")
        array_layout.addWidget(self.phase_label_energy, row, 0)
        self.phase_energy = QLineEdit("20")
        array_layout.addWidget(self.phase_energy, row, 1)
        self.phase_label_distance = QLabel("Distance (m):")
        array_layout.addWidget(self.phase_label_distance, row, 2)
        self.phase_distance = QLineEdit("0.5")
        array_layout.addWidget(self.phase_distance, row, 3)
        row += 1
        
        self.phase_label_pixelsize = QLabel("  Pixel size (um):")
        array_layout.addWidget(self.phase_label_pixelsize, row, 0)
        self.phase_pixelsize = QLineEdit("5.5")
        array_layout.addWidget(self.phase_pixelsize, row, 1)
        self.phase_label_deltabeta = QLabel("Delta/Beta:")
        array_layout.addWidget(self.phase_label_deltabeta, row, 2)
        self.phase_deltabeta = QLineEdit("200")
        array_layout.addWidget(self.phase_deltabeta, row, 3)
        row += 1
        
        # Ring removal params
        self.ring_check = QCheckBox("Enable Ring Removal")
        self.ring_check.setChecked(False)
        self.ring_check.stateChanged.connect(self.update_ring_state)
        array_layout.addWidget(self.ring_check, row, 0, 1, 2)
        row += 1
        
        self.ring_label_hsigma = QLabel("  Horizontal sigma:")
        array_layout.addWidget(self.ring_label_hsigma, row, 0)
        self.ring_hsigma = QLineEdit("3")
        array_layout.addWidget(self.ring_hsigma, row, 1)
        self.ring_label_vsigma = QLabel("Vertical sigma:")
        array_layout.addWidget(self.ring_label_vsigma, row, 2)
        self.ring_vsigma = QLineEdit("1")
        array_layout.addWidget(self.ring_vsigma, row, 3)
        row += 1

        # Z ROI params
        self.zroi_check = QCheckBox("Enable Z ROI")
        self.zroi_check.setChecked(False)
        self.zroi_check.stateChanged.connect(self.update_zroi_state)
        array_layout.addWidget(self.zroi_check, row, 0, 1, 2)
        row += 1
        
        self.zroi_label_start = QLabel("  Start:")
        array_layout.addWidget(self.zroi_label_start, row, 0)
        self.zroi_start = QLineEdit("250")
        array_layout.addWidget(self.zroi_start, row, 1)
        self.zroi_label_height = QLabel("Height:")
        array_layout.addWidget(self.zroi_label_height, row, 2)
        self.zroi_height = QLineEdit("300")
        array_layout.addWidget(self.zroi_height, row, 3)
        self.zroi_label_step = QLabel("Step:")
        array_layout.addWidget(self.zroi_label_step, row, 4)
        self.zroi_step = QLineEdit("1")
        array_layout.addWidget(self.zroi_step, row, 5)
        row += 1

        # Crop params
        self.crop_check = QCheckBox("Enable Crop")
        self.crop_check.setChecked(False)
        self.crop_check.stateChanged.connect(self.update_crop_state)
        array_layout.addWidget(self.crop_check, row, 0, 1, 2)
        row += 1
        
        self.crop_label_x = QLabel("  X:")
        array_layout.addWidget(self.crop_label_x, row, 0)
        self.crop_x = QLineEdit("1020")
        array_layout.addWidget(self.crop_x, row, 1)
        self.crop_label_y = QLabel("Y:")
        array_layout.addWidget(self.crop_label_y, row, 2)
        self.crop_y = QLineEdit("396")
        array_layout.addWidget(self.crop_y, row, 3)
        row += 1
        
        self.crop_label_width = QLabel("  Width:")
        array_layout.addWidget(self.crop_label_width, row, 0)
        self.crop_width = QLineEdit("2500")
        array_layout.addWidget(self.crop_width, row, 1)
        self.crop_label_length = QLabel("Length:")
        array_layout.addWidget(self.crop_label_length, row, 2)
        self.crop_length = QLineEdit("2500")
        array_layout.addWidget(self.crop_length, row, 3)
        row += 1

        # Additional rotation angle (Dynamic CT only) - three separate fields
        self.rotate_check_label = QLabel("Additional rotation angle (Z, X, Y):")
        array_layout.addWidget(self.rotate_check_label, row, 0, 1, 2)
        row += 1
        self.rotate_label_z = QLabel("  Z:")
        array_layout.addWidget(self.rotate_label_z, row, 0)
        self.rotate_z = QLineEdit("0")
        array_layout.addWidget(self.rotate_z, row, 1)
        self.rotate_label_x = QLabel("X:")
        array_layout.addWidget(self.rotate_label_x, row, 2)
        self.rotate_x = QLineEdit("0")
        array_layout.addWidget(self.rotate_x, row, 3)
        self.rotate_label_y = QLabel("Y:")
        array_layout.addWidget(self.rotate_label_y, row, 4)
        self.rotate_y = QLineEdit("0")
        array_layout.addWidget(self.rotate_y, row, 5)
        row += 1

        # Clip histogram
        array_layout.addWidget(QLabel("Clip histogram:"), row, 0)
        row += 1
        array_layout.addWidget(QLabel("  Bit depth:"), row, 0)
        self.clip_bitdepth = QComboBox()
        self.clip_bitdepth.addItems(["8", "16", "32"])
        self.clip_bitdepth.setCurrentText("32")
        self.clip_bitdepth.currentTextChanged.connect(self.update_cliphist_state)
        array_layout.addWidget(self.clip_bitdepth, row, 1)
        self.clip_label_min = QLabel("Min:")
        array_layout.addWidget(self.clip_label_min, row, 2)
        self.clip_min = QLineEdit("-1.54e-7")
        array_layout.addWidget(self.clip_min, row, 3)
        self.clip_label_max = QLabel("Max:")
        array_layout.addWidget(self.clip_label_max, row, 4)
        self.clip_max = QLineEdit("1.712e-6")
        array_layout.addWidget(self.clip_max, row, 5)
        row += 1

        array_group.setLayout(array_layout)
        layout.addWidget(array_group)
        
        # === COMMAND OUTPUT ===
        command_group = QGroupBox("Generated Command")
        command_layout = QVBoxLayout()
        command_layout.setContentsMargins(5, 5, 5, 5)
        command_layout.setSpacing(2)
        
        self.recon_command_text = QTextEdit()
        self.recon_command_text.setMaximumHeight(60)
        self.recon_command_text.setReadOnly(True)
        command_layout.addWidget(self.recon_command_text)
        
        command_group.setLayout(command_layout)
        layout.addWidget(command_group)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        
        batch_btn = QPushButton("Make Batch Script")
        batch_btn.clicked.connect(lambda: self.open_batch_editor(self.recon_command_text))
        batch_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(batch_btn)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self.copy_command(self.recon_command_text))
        button_layout.addWidget(copy_btn)
        
        run_btn = QPushButton("Run Command")
        run_btn.clicked.connect(lambda: self.run_command(self.recon_command_text))
        run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(run_btn)
        
        layout.addLayout(button_layout)
        
        # Connect all input fields to auto-generate command
        for widget in [self.flatsdarks_edit, self.tomo_edit, self.save_edit, self.temp_edit,
                      self.number_edit, self.cor_edit,
                      self.rotate_z, self.rotate_x, self.rotate_y,
                      self.timeseries_edit,
                      self.timelapse_edit,
                      self.zroi_start, self.zroi_height, self.zroi_step,
                      self.crop_x, self.crop_y, self.crop_width, self.crop_length,
                      self.phase_energy, self.phase_distance, self.phase_pixelsize, self.phase_deltabeta,
                      self.ring_hsigma, self.ring_vsigma,
                      self.reduce_target,
                      self.spot_thresh, self.spot_sigma,
                      self.clip_min, self.clip_max]:
            widget.textChanged.connect(self.generate_reconstruction_command)

        # Scan tomo dir when tomo path changes
        self.tomo_edit.textChanged.connect(self.scan_tomo_dir)
        
        # Set initial enabled states
        self.update_mode_state()
        self.update_zroi_state()
        self.update_crop_state()
        self.update_phase_state()
        self.update_ring_state()
        self.update_reduce_state()
        self.update_spot_state()
        self.update_cliphist_state()
        # Generate initial command
        self.generate_reconstruction_command()
        
        return tab
    
    def create_reslicing_tab(self):
        """Create the reslicing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # === PATH GROUP ===
        path_group = QGroupBox("Path")
        path_layout = QGridLayout()
        
        path_layout.addWidget(QLabel("Reconstruction path:"), 0, 0)
        self.reslice_path_edit = QLineEdit("")
        path_layout.addWidget(self.reslice_path_edit, 0, 1)
        path_btn = QPushButton("Browse")
        path_btn.clicked.connect(lambda: self.browse_folder(self.reslice_path_edit))
        path_layout.addWidget(path_btn, 0, 2)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # === MODE GROUP ===
        mode_group = QGroupBox("Reslicing Mode")
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        
        self.reslice_mode_group = QButtonGroup()
        
        self.reslice_dct_radio = QRadioButton("Dynamic CT")
        self.reslice_dct_radio.setChecked(True)
        self.reslice_mode_group.addButton(self.reslice_dct_radio)
        mode_layout.addWidget(self.reslice_dct_radio)
        
        self.reslice_tlct_radio = QRadioButton("Time-lapse CT")
        self.reslice_mode_group.addButton(self.reslice_tlct_radio)
        mode_layout.addWidget(self.reslice_tlct_radio)
        
        mode_layout.addStretch()
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # === SLICE PARAMETERS GROUP ===
        slice_group = QGroupBox("Slice Parameters")
        slice_layout = QGridLayout()
        
        # XY slice
        self.xy_check = QCheckBox("Enable XY slice")
        self.xy_check.setChecked(True)
        self.xy_check.stateChanged.connect(self.update_reslice_state)
        slice_layout.addWidget(self.xy_check, 0, 0)
        slice_layout.addWidget(QLabel("Position:"), 0, 1)
        self.xy_position = QLineEdit("450")
        slice_layout.addWidget(self.xy_position, 0, 2)
        
        # XZ slice
        self.xz_check = QCheckBox("Enable XZ slice")
        self.xz_check.setChecked(True)
        self.xz_check.stateChanged.connect(self.update_reslice_state)
        slice_layout.addWidget(self.xz_check, 1, 0)
        slice_layout.addWidget(QLabel("Position:"), 1, 1)
        self.xz_position = QLineEdit("1200")
        slice_layout.addWidget(self.xz_position, 1, 2)
        
        # YZ slice
        self.yz_check = QCheckBox("Enable YZ slice")
        self.yz_check.setChecked(False)
        self.yz_check.stateChanged.connect(self.update_reslice_state)
        slice_layout.addWidget(self.yz_check, 2, 0)
        slice_layout.addWidget(QLabel("Position:"), 2, 1)
        self.yz_position = QLineEdit("1200")
        slice_layout.addWidget(self.yz_position, 2, 2)
        
        slice_group.setLayout(slice_layout)
        layout.addWidget(slice_group)
        
        # === COMMAND OUTPUT ===
        command_group = QGroupBox("Generated Command")
        command_layout = QVBoxLayout()
        command_layout.setContentsMargins(5, 5, 5, 5)
        command_layout.setSpacing(2)
        
        self.reslice_command_text = QTextEdit()
        self.reslice_command_text.setMaximumHeight(60)
        self.reslice_command_text.setReadOnly(True)
        command_layout.addWidget(self.reslice_command_text)
        
        command_group.setLayout(command_layout)
        layout.addWidget(command_group)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        
        batch_btn = QPushButton("Make Batch Script")
        batch_btn.clicked.connect(lambda: self.open_batch_editor(self.reslice_command_text))
        batch_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(batch_btn)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self.copy_command(self.reslice_command_text))
        button_layout.addWidget(copy_btn)
        
        run_btn = QPushButton("Run Command")
        run_btn.clicked.connect(lambda: self.run_command(self.reslice_command_text))
        run_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(run_btn)
        
        layout.addLayout(button_layout)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Connect inputs to auto-generate command
        self.reslice_path_edit.textChanged.connect(self.generate_reslice_command)
        self.xy_position.textChanged.connect(self.generate_reslice_command)
        self.xz_position.textChanged.connect(self.generate_reslice_command)
        self.yz_position.textChanged.connect(self.generate_reslice_command)
        self.reslice_dct_radio.toggled.connect(self.generate_reslice_command)
        
        # Set initial state
        self.update_reslice_state()
        
        # Generate initial command
        self.generate_reslice_command()
        
        return tab
    
    def update_mode_state(self):
        """Enable/disable fields based on CT mode selection"""
        is_dynamic = self.dynamic_radio.isChecked()
        
        # Enable rotation fields for Dynamic CT
        for w in [self.rotate_check_label, self.rotate_label_z, self.rotate_z,
                  self.rotate_label_x, self.rotate_x, self.rotate_label_y, self.rotate_y]:
            w.setEnabled(is_dynamic)

        self.timeseries_label.setEnabled(is_dynamic)
        self.timeseries_edit.setEnabled(is_dynamic)
        
        # Enable timelapse search for Time-lapse CT
        self.timelapse_label.setEnabled(not is_dynamic)
        self.timelapse_edit.setEnabled(not is_dynamic)
        
        self.generate_reconstruction_command()
    
    def update_zroi_state(self):
        enabled = self.zroi_check.isChecked()
        self.zroi_label_start.setEnabled(enabled)
        self.zroi_start.setEnabled(enabled)
        self.zroi_label_height.setEnabled(enabled)
        self.zroi_height.setEnabled(enabled)
        self.zroi_label_step.setEnabled(enabled)
        self.zroi_step.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_crop_state(self):
        enabled = self.crop_check.isChecked()
        self.crop_label_x.setEnabled(enabled)
        self.crop_x.setEnabled(enabled)
        self.crop_label_y.setEnabled(enabled)
        self.crop_y.setEnabled(enabled)
        self.crop_label_width.setEnabled(enabled)
        self.crop_width.setEnabled(enabled)
        self.crop_label_length.setEnabled(enabled)
        self.crop_length.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_phase_state(self):
        enabled = self.phase_check.isChecked()
        self.phase_label_energy.setEnabled(enabled)
        self.phase_energy.setEnabled(enabled)
        self.phase_label_distance.setEnabled(enabled)
        self.phase_distance.setEnabled(enabled)
        self.phase_label_pixelsize.setEnabled(enabled)
        self.phase_pixelsize.setEnabled(enabled)
        self.phase_label_deltabeta.setEnabled(enabled)
        self.phase_deltabeta.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_ring_state(self):
        enabled = self.ring_check.isChecked()
        self.ring_label_hsigma.setEnabled(enabled)
        self.ring_hsigma.setEnabled(enabled)
        self.ring_label_vsigma.setEnabled(enabled)
        self.ring_vsigma.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_reduce_state(self):
        enabled = self.reduce_check.isChecked()
        self.reduce_label_target.setEnabled(enabled)
        self.reduce_target.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_spot_state(self):
        enabled = self.spot_check.isChecked()
        self.spot_label_thresh.setEnabled(enabled)
        self.spot_thresh.setEnabled(enabled)
        self.spot_label_sigma.setEnabled(enabled)
        self.spot_sigma.setEnabled(enabled)
        self.generate_reconstruction_command()

    def update_cliphist_state(self):
        enabled = self.clip_bitdepth.currentText() != "32"
        self.clip_label_min.setEnabled(enabled)
        self.clip_min.setEnabled(enabled)
        self.clip_label_max.setEnabled(enabled)
        self.clip_max.setEnabled(enabled)
        self.generate_reconstruction_command()
    
    def update_reslice_state(self):
        """Enable/disable reslice position fields based on checkboxes"""
        self.xy_position.setEnabled(self.xy_check.isChecked())
        self.xz_position.setEnabled(self.xz_check.isChecked())
        self.yz_position.setEnabled(self.yz_check.isChecked())
        self.generate_reslice_command()
    
    def update_paths_from_project(self):
        import re
        prj = self.project_edit.text().strip()
        pattern = re.compile(r'^(\d{2})([GRMPEBgrmpeb])(\d{5})$')
        match = pattern.match(prj)
        if match:
            access_map = {
                'G': 'General user', 'R': 'Rapid access', 'M': 'Maintenance',
                'P': 'Paid access',  'E': 'Education',    'B': 'Beam team',
            }
            access = access_map[match.group(2).upper()]
            self.project_status.setText(f"Cycle {match.group(1)} · {access}")
            self.project_status.setStyleSheet("color: green; font-style: italic;")
            base = f"/beamlinedata/BMIT/projects/prj{prj}"
            self.flatsdarks_edit.setText(f"{base}/raw")
            self.tomo_edit.setText(f"{base}/raw")
            self.save_edit.setText(f"{base}/rec")
            self.temp_edit.setText(f"{base}/raw-preprocessed/test-temp")
        else:
            if prj:
                self.project_status.setText("Invalid format")
                self.project_status.setStyleSheet("color: red; font-style: italic;")
            else:
                self.project_status.setText("")
                self.project_status.setStyleSheet("color: grey; font-style: italic;")
        self.generate_reconstruction_command()

    def scan_tomo_dir(self):
        """Read tomo subfolder to populate width, height, and number of projections."""
        tomo_path = self.tomo_edit.text().strip()
        if os.path.isdir(os.path.join(tomo_path, 'tomo')):
            tomodir = os.path.join(tomo_path, 'tomo')
        elif os.path.isdir(tomo_path):
            tomodir = tomo_path
        else:
            self.info_width.setText("—")
            self.info_height.setText("—")
            self.info_number.setText("—")
            return
        try:
            files = sorted([
                f for f in os.listdir(tomodir)
                if os.path.isfile(os.path.join(tomodir, f))
            ])
            if not files:
                raise ValueError("No files found")
            with tifffile.TiffFile(os.path.join(tomodir, files[0])) as tif:
                pages_per_file = len(tif.pages)
                height, width = tif.pages[0].shape[0], tif.pages[0].shape[1]
                is_bigtiff = tif.is_bigtiff
            if is_bigtiff or pages_per_file > 1:
                number = sum(
                    len(tifffile.TiffFile(os.path.join(tomodir, f)).pages)
                    for f in files
                )
            else:
                number = len(files)
            self.info_width.setText(str(width))
            self.info_height.setText(str(height))
            self.info_number.setText(str(number))
        except Exception as e:
            self.info_width.setText("error")
            self.info_height.setText("error")
            self.info_number.setText(str(e))

    def browse_folder(self, line_edit):
        # Get the current path from the line edit
        current_path = line_edit.text()
        
        # Check if the current path exists, otherwise use root
        if current_path and os.path.isdir(current_path):
            start_path = current_path
        else:
            start_path = "/"
        
        # Open dialog at the determined path
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", start_path)
        if folder:
            line_edit.setText(folder)
    
    def generate_reconstruction_command(self):
        # Determine which script to use based on mode
        if self.dynamic_radio.isChecked():
            script_name = "tofu-dCT.py"
        else:
            script_name = "tofu-tlCT.py"
        
        cmd_parts = [f"python {script_name}"]
        
        # Add path parameters
        if self.flatsdarks_edit.text():
            cmd_parts.append(f'-flatsdarks {self.flatsdarks_edit.text()}')
        if self.tomo_edit.text():
            cmd_parts.append(f'-tomo {self.tomo_edit.text()}')
        if self.save_edit.text():
            cmd_parts.append(f'-SAVE {self.save_edit.text()}')
        if self.temp_edit.text():
            cmd_parts.append(f'-TEMP {self.temp_edit.text()}')
        
        # Add basic parameters
        cmd_parts.append(f'-number {self.number_edit.text()}')
        cmd_parts.append(f'-CoR {self.cor_edit.text()}')
        
        # Add mode-specific parameters
        if self.dynamic_radio.isChecked():
            # Dynamic CT parameters
            cmd_parts.append(f'-rotate="{self.rotate_z.text()},{self.rotate_x.text()},{self.rotate_y.text()}"')
            cmd_parts.append(f'-timeseries {self.timeseries_edit.text()}')
        else:
            # Time-lapse CT parameters
            if self.timelapse_edit.text():
                cmd_parts.append(f'-timelapsesearch {self.timelapse_edit.text()}')
        
        # Add reduce params
        reduce_enabled = "1" if self.reduce_check.isChecked() else "0"
        reduce_params = f'{reduce_enabled},{self.reduce_target.text()}'
        cmd_parts.append(f'-reduce {reduce_params}')
        
        # Add Z ROI params
        zroi_enabled = "1" if self.zroi_check.isChecked() else "0"
        zroi_params = f'{zroi_enabled},{self.zroi_start.text()},{self.zroi_height.text()},{self.zroi_step.text()}'
        cmd_parts.append(f'-zroiparams {zroi_params}')
        
        # Add crop params
        crop_enabled = "1" if self.crop_check.isChecked() else "0"
        crop_params = f'{crop_enabled},{self.crop_x.text()},{self.crop_y.text()},{self.crop_width.text()},{self.crop_length.text()}'
        cmd_parts.append(f'-cropparams {crop_params}')
        
        # Add phase params
        phase_enabled = "1" if self.phase_check.isChecked() else "0"
        phase_params = f'{phase_enabled},{self.phase_energy.text()},{self.phase_distance.text()},{self.phase_pixelsize.text()},{self.phase_deltabeta.text()}'
        cmd_parts.append(f'-phaseparams {phase_params}')
        
        # Add ring removal params
        ring_enabled = "1" if self.ring_check.isChecked() else "0"
        ring_params = f'{ring_enabled},{self.ring_hsigma.text()},{self.ring_vsigma.text()}'
        cmd_parts.append(f'-ringremovalparams {ring_params}')
        
        # Add bright spot params
        spot_enabled = "1" if self.spot_check.isChecked() else "0"
        spot_params = f'{spot_enabled},{self.spot_thresh.text()},{self.spot_sigma.text()}'
        cmd_parts.append(f'-brightspotparams {spot_params}')
        
        # Add clip histogram
        clip_params = f'{self.clip_bitdepth.currentText()},{self.clip_min.text()},{self.clip_max.text()}'
        cmd_parts.append(f'-cliphist {clip_params}')

        command = " ".join(cmd_parts)
        self.recon_command_text.setPlainText(command)
        
        return command
    
    def generate_reslice_command(self):
        """Generate the reslicing command"""
        cmd_parts = ["python reslice.py"]
        
        # Add path
        if self.reslice_path_edit.text():
            cmd_parts.append(f'-PATH {self.reslice_path_edit.text()}')
        
        # Add XY slice params
        xy_enabled = "1" if self.xy_check.isChecked() else "0"
        cmd_parts.append(f'-XYsli {xy_enabled},{self.xy_position.text()}')
        
        # Add XZ slice params
        xz_enabled = "1" if self.xz_check.isChecked() else "0"
        cmd_parts.append(f'-XZsli {xz_enabled},{self.xz_position.text()}')
        
        # Add YZ slice params
        yz_enabled = "1" if self.yz_check.isChecked() else "0"
        cmd_parts.append(f'-YZsli {yz_enabled},{self.yz_position.text()}')
        
        # Add mode (0 for dCT, 1 for tlCT)
        mode = "0" if self.reslice_dct_radio.isChecked() else "1"
        cmd_parts.append(f'-mode {mode}')
        
        command = " ".join(cmd_parts)
        self.reslice_command_text.setPlainText(command)
        
        return command
    
    def open_batch_editor(self, command_text_widget):
        """Open the batch script editor"""
        editor = BatchScriptEditor(self)
        editor.show()  # Use show() instead of exec_() to keep it non-modal
    
    def copy_command(self, text_widget):
        command = text_widget.toPlainText()
        if command:
            clipboard = QApplication.clipboard()
            clipboard.setText(command)
            QMessageBox.information(self, "Success", "Command copied to clipboard!")
    
    def run_command(self, text_widget):
        command = text_widget.toPlainText()
        if not command:
            return
        
        try:
            # Show message that process is starting
            print("\n" + "="*80)
            print("Running command:")
            print(command)
            print("="*80 + "\n")
            
            # Run the command WITHOUT capturing output - it will print to terminal
            subprocess.run(command, shell=True)
            
            print("\n" + "="*80)
            print("Command execution completed")
            print("="*80 + "\n")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run command:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    # Set application style
    app.setStyle('Fusion')
    window = CTReconstructionGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()