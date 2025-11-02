# BAT Predictive Text Dumper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Basilabt/iOS_PredictiveText_Dumper/blob/main/LICENSE)
[![Developer](https://img.shields.io/badge/Developer-Basilabt-crimson)](https://github.com/Basilabt)
![Version](https://img.shields.io/badge/version-1.0-brightgreen)
![Language](https://img.shields.io/badge/language-Python-blue)


## Table of Contents

- [Preview](#preview)
- [Requirements](#requirements)
- [Description](#description)
- [Installation](#installation)
- [Contact](#contact)

## Preview
<img width="1566" height="741" alt="Image" src="https://github.com/user-attachments/assets/88d215df-c6e6-4975-bb32-5ae3c29ab712" />

## Requirements
- Linux or macOS environment  
- Jailbroken iOS device with SSH access  

## Description
A simple Python script to **download predictive text and keyboard data** from iOS systems.

The tool connects to your device via SSH, scans the `/var/mobile/Library/Keyboard` directory for predictive-text and lexicon files, and downloads them for analysis.

It detects and retrieves files such as:

- `UserDictionary.sqlite`  
- `*-dynamic-text.dat`  
- `*.lexicon`  
- `Lexicon.plist`  

All downloaded files are saved into a timestamped folder for easy organization.

## Installation

```
# 1. Clone the repository
  > git clone https://github.com/Basilabt/iOS_PredictiveText_Dumper

# 2. Navigate to the project directory
  > cd iOS_PredictiveText_Dumper/Script

# 3. Run the tool
  > python3 main.py
```

## Contact
If you have any questions, suggestions, or feedback

- **Email:** [baabutaleb@gmail.com](mailto:baabutaleb@gmail.com)
- **GitHub:** [https://github.com/Basilabt](https://github.com/Basilabt)
