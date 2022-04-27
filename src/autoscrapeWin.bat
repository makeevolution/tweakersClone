:: schtasks /create /sc minute /mo 5 /tn test /tr C:\Users\Hp\tweakersClone\src\automate.bat
:: schtasks /delete /tn test
:: .\venv_scraperLaptop\Scripts\activate.bat

set workDir="C:\Users\aldo-\OneDrive\job and portfolio\onlineWebscraperAutoScrape\src\"
cd %workDir%
rasdial "PrivateVPN IKEv2" "aldo_hasibuan@yahoo.com" "PrivateVPN123@@"
.\env_ROG\Scripts\python.exe scrapePeriodically.py
rasdial "PrivateVPN IKEv2" /disconnect