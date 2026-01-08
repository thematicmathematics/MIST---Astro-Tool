# 🔭 M.I.S.T (Minima Identification Search Tool)

**Developer:** S. Ceren Caliskan  
**Context:** Astrophysics MSc Thesis Project (Canakkale Onsekiz Mart University)  
**Status:** v1.0 (Stable Source Code)

## 🌌 About the Project
**M.I.S.T** is an open-source tool developed to analyze the light curves of eclipsing binary stars, automatically detect their minimum times, and generate data for O-C (Open-C) analyses.
It combines both classical methods and modern data processing processes in a single interface:
* **Kwee-van Woerden (KvW) Method**
* **Parabolic Fitting Method**
* **Machine Learning Data Export**

<img width="631" height="1013" alt="image" src="https://github.com/user-attachments/assets/c56ea96b-92c6-42a5-b2d7-4e6bb2e6288f" />


## 🚀 Key Features 
* **Automated Detection:** Automatically scans for primary and secondary minima in the light curve.
* **Error Analysis:** Calculates error margins using Monte Carlo simulations.
* **Hybrid Analysis:** Simultaneously applies and compares KvW and Parabolic methods.
* **User-Friendly GUI:** Modern interface based on PyQt6 with dark mode.
* 
## 🛠️ Installation & Usage 
M.I.S.T. has been shared as "Source Code" for the purposes of scientific transparency and security. You need the Python environment to run it.
### Requirements 
* **Python 3.10** or higher
* Libraries: `numpy`, `matplotlib`, `scipy`, `PyQt6`

### ⚡ Quick Start 
**Method 1: Using Spyder/PyCharm**
1. Download the files by clicking the green **`<> Code`** button on this page and selecting **Download ZIP**.
2. Extract the folder to your desktop.
3. Open the `mist.py` file with **Spyder** or your IDE and press **Run (F5)**.

**Method 2: Using Terminal**
Open a terminal/command prompt inside the folder, first install the libraries, then start the program:
```bash
pip install -r requirements.txt
python mist.py
```

🎓 Citation
This software has been developed for scientific research. If you use it in your studies, please cite it as follows:

> Caliskan, S. C. (2026). *M.I.S.T: Minima Identification Search Tool*. MSc Thesis Project. GitHub Repository. https://github.com/thematicmathematics/MIST---Astro-Tool

License
This project is licensed under the MIT License - see the LICENSE file for details.
