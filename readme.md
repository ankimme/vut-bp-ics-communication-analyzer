# ICS Analyzer

## Spuštění aplikace

Aplikace vyžaduje instalaci jazyka Python ve verzi 3.10 nebo vyšší. V ubuntu 22.04 je verze nainstalována už v základu. Pro starší verze systému je potřeba verzi doinstalovat následujícími příkazy:

```
sudo apt update && sudo apt upgrade -y
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.10
```

Pro prvotní spuštění aplikace je potřeba provést následující kroky ve složce `ics_analyzer`:

```
python3.10 -m venv env/
source env_new/bin/activate
pip install -r requirements.txt
./main.py
```

Pro další spuštění již stačí pouze tyto kroky:
```
source env_new/bin/activate
./main.py
```

Pozn: v ubuntu 22.04 lze příkaz `python3.10` nahradit příkazem `python3`