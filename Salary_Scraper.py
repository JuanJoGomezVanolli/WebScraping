#We make any necesary imports
# We import the needed libraries
# In the case that you are getting errors from the requests library. Add the line: "-m pip install requests" instead of "import requests"

import tkinter as tk
from tkinter.ttk import *
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from ttkthemes import ThemedTk
from PIL import ImageTk, Image


# Here we place all formulas
#____________________________________________________________

#We create the link url string from 5 inputs requested to the user in the main program UI (Job Title, Page Number, Location, Job Family, and Radius)

def createLinkURL(jobTitleText, pageNum,locationText,jobFamilytext,Radium):
  new_JT = jobTitleText.replace(" ", "%20")
  url = ""
  if (jobTitleText == "N/A" and locationText == "N/A" and jobFamilytext == "N/A" ): # En el caso que todos sean N/A
    url = "https://www.pracuj.pl/praca?sal=1"

  elif (jobTitleText != "N/A" and locationText == "N/A" and jobFamilytext == "N/A" ): # En el caso que solo sea Job title
    url = "https://www.pracuj.pl/praca/" + jobTitleText + ";kw?sal=1&pn=" + pageNum

  elif (jobTitleText == "N/A" and locationText != "N/A" and jobFamilytext == "N/A" ): # En el caso que solo sea Location
    url = "https://www.pracuj.pl/praca/" + locationText + ";wp?rd=" + Radium + "&sal=1&pn=" + pageNum

  elif (jobTitleText == "N/A" and locationText == "N/A" and jobFamilytext != "N/A" ): # En el caso que solo sea Job Family
    url = "https://www.pracuj.pl/praca/" + jobFamilytext + "?sal=1&pn=" + pageNum

  elif (jobTitleText != "N/A" and locationText != "N/A" and jobFamilytext == "N/A" ): # En el caso que sean jobTitle y location
    url = "https://www.pracuj.pl/praca/" + jobTitleText + ";kw/" + locationText + ";wp" + "?rd=" + Radium + "&sal=1&pn=" + pageNum

  elif (jobTitleText == "N/A" and locationText != "N/A" and jobFamilytext != "N/A" ): # En el caso que sean location y Job Family
    url = "https://www.pracuj.pl/praca/" + locationText + ";wp/" + jobFamilytext + "?rd=" + Radium + "&sal=1&pn=" + pageNum

  elif (jobTitleText != "N/A" and locationText == "N/A" and jobFamilytext != "N/A" ): # En el caso quie sea Job Title y Job Family
    url = "https://www.pracuj.pl/praca/" + jobTitleText + ";kw/" + jobFamilytext + "?sal=1&pn=" + pageNum

  elif (jobTitleText != "N/A" and locationText != "N/A" and jobFamilytext != "N/A" ): # En el caso que sean todos al mismo tiempo
    url = "https://www.pracuj.pl/praca/" + jobTitleText + ";kw/" + locationText + ";wp/" + jobFamilytext + "?rd=" + Radium + "&sal=1&pn=" + pageNum

  return url



 #This function recieves a string and eleminates each instance of the string '\xa0' for a space ' '.
def removeSpaceCharacter_string(input_string):
    # Remove non-breaking spaces
    transformed_string = input_string.replace('\xa0', '')

    return transformed_string


#This function recieves a string and returns just the numbers that are before the simbol zł.
#This numbers are going to be the salary range. Sometimes they can separated like this 1234-1231 or just one number.
def getRawSalaryRange_numbers(string):
    result = ""
    for char in string:
        if char != 'z' and char != 'ł':
            result += char
        else:
            break
    return result


#This function separates each number in a diferent variable and returns it. We recieve for example the number 12313-123123 and we return two variables 12313 and 123123.
def separateNumbers(string):
  if ("–" in string) or ("-" in string) :
    parts = string.split("–")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    else:
        return None, None
  else:
    return string, string


#This function takes an array of strings with the numbers without separating (i.e 123-123) and returns a new array which contians two variables in each index which are the salary range.
def fill_salaryDb(stringArr):
  newTextArr = []
  for string in stringArr:
    newString = separateNumbers(getRawSalaryRange_numbers(string))
    newTextArr.append(newString)
  return newTextArr

#This function takes a specific number of string arrays and fills a dataframe (column) with the values of the arrays
def populate_dataframe(data, locations, companies, jobTitles, frecuency):
    df = pd.DataFrame(data, columns=['Min', 'Max'])
    df['Per Month / Per Hour'] = frecuency
    df['Location'] = locations
    df['Company'] = companies
    df['Job Title'] = jobTitles
    df['Min'] = df['Min'].str.replace(',','.')
    df['Max'] = df['Max'].str.replace(',','.')
    df['Min'] = pd.to_numeric(df['Min'])
    df['Max'] = pd.to_numeric(df['Max'])
    return df


#This function recieves a soup object (Parsed HTML) and searches specific divs and spans to take the salary figures form the HTML.
def getSalaries(soup):
  job_salaries = []
  transformed_strings = []
  newSalaryArr = []
  for div in soup.find_all("div", {"class": "listing_b1evff58 listing_po9665q"}):
    for a in div.find_all("span", {"class": "listing_sug0jpb"}):
      job_salaries.append(a.text.strip())
  for job_titles in job_salaries:
    transformed_string = removeSpaceCharacter_string(job_titles)
    transformed_strings.append(transformed_string)

  for number in transformed_strings:
    newText = getRawSalaryRange_numbers(number)
    newSalaryArr.append(newText)
  return newSalaryArr


#This function recieves a soup object (Parsed HTML) and searches specific divs and spans to take the Location text.
def getLocation(soup):
  locationsArr = []
  backupLocations = []
  for div in soup.find_all("h5", {"class": "listing_t1e3cjpn size-caption listing_t1rst47b"}):
    backupLocations.append(get_substring(div.text.strip(),"Siedziba firmy"))

  for div in soup.find_all("div", {"class": "listing_c18jd7pe"}):
    if div.find_all("h5", {"class": "listing_rdl5oe8 size-caption listing_t1rst47b"}):
      locationsArr.append(div.find_all("h5", {"class": "listing_rdl5oe8 size-caption listing_t1rst47b"})[0].text.strip())
    else:
      locationsArr.append(backupLocations[0])
      backupLocations.pop(0)
  return locationsArr


#This function recieves a soup object (Parsed HTML) and searches specific divs and spans to take the Company name text.
def getCompanies(soup):
  companyArr = []
  for div in soup.find_all("a", {"class": "listing_n194fgoq"}):
    for a in div.find_all("h4", {"class": "listing_eiims5z size-caption listing_t1rst47b"}):
      companyArr.append(a.text.strip())
  return companyArr


#This function recieves a soup object (Parsed HTML) and searches specific divs and spans to take the Job Title name text.
def getJobTitle(soup):
  jobTitleArr = []
  for div in soup.find_all("h2", {"class": "listing_buap3b6"}):
      jobTitleArr.append(div.text.strip())
  return jobTitleArr


#This function recieves a soup object (Parsed HTML) and searches specific divs and spans to take the salary frecuency text (by year or by month).
def getYearMonth(soup):
  newArrMonthyear = []
  finalArr = []
  for div in soup.find_all("div", {"class": "listing_b1evff58 listing_po9665q"}):
    for a in div.find_all("span", {"class": "listing_sug0jpb"}):
      newArrMonthyear.append(a.text.strip())
  for string in newArrMonthyear:
    if "godz" in string:
      finalArr.append("godz")
    else:
      finalArr.append("mies")
  return finalArr


#Function to extract text until a specific delimeter
def get_substring(input_string, delimiter):
    index = input_string.find(delimiter)
    if index != -1:
        return input_string[:index]
    else:
        return input_string

#Sometimes the specific webpage we are scraping reports the salary figures in another html div section. This function gets the location text in this case.
def getAditionalLocation(soup):
  locationsArr = []
  newLocationsArr = []
  for div in soup.find_all("h5", {"class": "listing_t1e3cjpn size-caption listing_t1rst47b"}):
    locationsArr.append(div.text.strip())
  for location in locationsArr:
    newText = get_substring(location,"Siedziba firmy")
    newLocationsArr.append(newText)

  return newLocationsArr

#Function that returns the value of a dictionary by recieving the dictionary and its key.
def find_value(dictionary , key):
    if key in dictionary:
        return dictionary[key]
    else:
        return "N/A"

#____________________________________________________________



#This is our main orchestrator function, called when clikcing the Generate button in the app
def generateDataDump():

    #We get the values of each input by the user
    jobTitleValue = JobTiitle.get()
    PageNumValue = PageNum.get()
    JobFamily = find_value(jobFam_map,JobFam.get())  ######
    LocationValue = Location.get()
    RadiousValue = Radious.get()
    FileNameValue = FileName.get()
    print("Value 1:", jobTitleValue)
    print("Value 2:", PageNumValue)
    print("Selected Variable:", type(JobFamily))
    print("Selected Location:", LocationValue)
    print("Selected Radious:", RadiousValue)
    print("Selected FileName:", FileNameValue)


    #We print the link we are going to parse just for debugging purposes
    print(createLinkURL(jobTitleValue, PageNumValue, LocationValue, JobFamily, RadiousValue))


    #We create the beautifoul soup object and parse it.
    url = createLinkURL(jobTitleValue, PageNumValue, LocationValue, JobFamily, RadiousValue)
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")

    #With the input data and parsed HTML we populate the dataframe to store the scraped data.
    populate_dataframe(fill_salaryDb(getSalaries(soup)), getLocation(soup), getCompanies(soup), getJobTitle(soup), getYearMonth(soup)).to_excel(FileNameValue + ".xlsx")





#This is a map in order for the user to select which job family he wants the data to be filtered.
jobFam_map = {
  "Administracja biurowa": "administracja%20biurowa;cc,5001",
  "        Sekretariat / Recepcja": "administracja%20biurowa;cc,5001/sekretariat%20recepcja;cc,5001001",
  "        Stanowiska asystenckie": "administracja%20biurowa;cc,5001/stanowiska%20asystenckie;cc,5001002",
  "        Tlumaczenia / Korekta": "administracja%20biurowa;cc,5001/tłumaczenia%20korekta;cc,5001003",
  "        Wprowdzanie / Przetwarzanie danych": "administracja%20biurowa;cc,5001/wprowadzanie%20przetwarzanie%20danych;cc,5001004",
  "        Wsparcie administracyjne": "administracja%20biurowa;cc,5001/wsparcie%20administracyjne;cc,5001005",
  "        Zarzadzanie biurem i administracja": "administracja%20biurowa;cc,5001/zarządzanie%20biurem%20i%20administracją;cc,5001006",
  "Badania i rozwoj": "badania%20i%20rozwój;cc,5002",
  "        Business Intelligence / Data Warehouse": "badania%20i%20rozwój;cc,5002/business%20intelligence%20data%20warehouse;cc,5002001",
  "        Chemia przemyslowa": "badania%20i%20rozw%C3%B3j;cc,5002/chemia%20przemys%C5%82owa;cc,5002002",
  "        Farmaceutyka / Biotechnologia": "badania%20i%20rozw%C3%B3j;cc,5002/farmaceutyka%20biotechnologia;cc,5002003",
  "        FMCG": "badania%20i%20rozw%C3%B3j;cc,5002/fmcg;cc,5002004",
  "        Tworzywa sztuczne": "badania%20i%20rozw%C3%B3j;cc,5002/tworzywa%20sztuczne;cc,5002006",
  "        Inne (Badania i rozwo)": "badania%20i%20rozw%C3%B3j;cc,5002/inne;cc,5002005",
  "Bankowosc" : "bankowo%C5%9B%C4%87;cc,5003",
  "        Analiza / Ryzyko" : "bankowo%C5%9B%C4%87;cc,5003/analiza%20ryzyko;cc,5003001",
  "        Bankowosc detaliczna" : "bankowo%C5%9B%C4%87;cc,5003/bankowo%C5%9B%C4%87%20detaliczna;cc,5003002",
  "        Bankowosc inwestcyjna" : "bankowo%C5%9B%C4%87;cc,5003/bankowo%C5%9B%C4%87%20inwestycyjna;cc,5003003",
  "        Bankowosc korporcyjna / SME" : "bankowo%C5%9B%C4%87;cc,5003/bankowo%C5%9B%C4%87%20korporacyjna%20sme;cc,5003004",
  "        Posrednictwo finansowe"  : "bankowo%C5%9B%C4%87;cc,5003/po%C5%9Brednictwo%20finansowe;cc,5003005",
  "BHP / Ochona srpdpwiska" : "bhp%20ochrona%20%C5%9Brodowiska;cc,5004",
  "        Inzynieria" : "bhp%20ochrona%20%C5%9Brodowiska;cc,5004/in%C5%BCynieria;cc,5004001",
  "        Nadzor" : "bhp%20ochrona%20%C5%9Brodowiska;cc,5004/nadz%C3%B3r;cc,5004002",
  "        Specjalisci / Konsultanci" : "bhp%20ochrona%20%C5%9Brodowiska;cc,5004/specjali%C5%9Bci%20konsultanci;cc,5004003",
  "Budownictwo" : "budownictwo;cc,5005",
  "        Architektura / Projektowanie" : "budownictwo;cc,5005/architektura%20projektowanie;cc,5005001",
  "        Ekologiczne" : "budownictwo;cc,5005/ekologiczne;cc,5005002",
  "        Energetyczne" : "budownictwo;cc,5005/energetyczne;cc,5005003",
  "        Infrastrukturalne" : "budownictwo;cc,5005/infrastrukturalne;cc,5005004",
  "        Instalacje" : "budownictwo;cc,5005/instalacje;cc,5005005",
  "        Mieszkaniowe / Przemysłowe" : "budownictwo;cc,5005/mieszkaniowe%20przemys%C5%82owe;cc,5005006",
  "Call Center" : "call%20center;cc,5006",
  "        Przychodzące" : "call%20center;cc,5006/przychodz%C4%85ce;cc,5006001",
  "        Wychodzące" : "call%20center;cc,5006/wychodz%C4%85ce;cc,5006002",
  "Doradztwo / Konsulting" : "doradztwo%20konsulting;cc,5037",
  "        Finanse" : "doradztwo%20konsulting;cc,5037/finanse;cc,5037001",
  "        Podatki / prawo" : "doradztwo%20konsulting;cc,5037/podatki%20prawo;cc,5037002",
  "        Sektor publiczny" : "doradztwo%20konsulting;cc,5037/sektor%20publiczny;cc,5037003",
  "        IT/Telekomunikacja" : "doradztwo%20konsulting;cc,5037/ittelekomunikacja;cc,5037004",
  "        Biznes/Strategia" : "doradztwo%20konsulting;cc,5037/biznesstrategia;cc,5037005",
  "        Inne (Doradztwo / Konsulting)" : "doradztwo%20konsulting;cc,5037/inne;cc,5037006",
  "Energetyka" : "energetyka;cc,5036",
  "        Budownictwo (Energetyka)" : "energetyka;cc,5036/budownictwo;cc,5036001",
  "        Konwencjonalna" : "energetyka;cc,5036/konwencjonalna;cc,5036002",
  "        Nafta i gaz" : "energetyka;cc,5036/nafta%20i%20gaz;cc,5036003",
  "        Odnawialna" : "energetyka;cc,5036/odnawialna;cc,5036004",
  "Edukacja / Szkolenia" : "edukacja%20szkolenia;cc,5007",
  "        Nauka języków obcych" : "edukacja%20szkolenia;cc,5007/nauka%20j%C4%99zyk%C3%B3w%20obcych;cc,5007001",
  "        Szkolenia / Rozwój osobisty" : "edukacja%20szkolenia;cc,5007/szkolenia%20rozw%C3%B3j%20osobisty;cc,5007002",
  "        Szkolnictwo" : "edukacja%20szkolenia;cc,5007/szkolnictwo;cc,5007003",
  "Finanse / Ekonomia" : "finanse%20ekonomia;cc,5008",
  "        Audyt / Podatki" : "finanse%20ekonomia;cc,5008/audyt%20podatki;cc,5008001",
  "        Doradztwo / Konsulting" : "finanse%20ekonomia;cc,5008/doradztwo%20konsulting;cc,5008002",
  "        Kontroling" : "finanse%20ekonomia;cc,5008/kontroling;cc,5008004",
  "        Księgowość" : "finanse%20ekonomia;cc,5008/ksi%C4%99gowo%C5%9B%C4%87;cc,5008005",
  "        Rynki kapitałowe" : "finanse%20ekonomia;cc,5008/rynki%20kapita%C5%82owe;cc,5008006",
  "        Analiza" : "finanse%20ekonomia;cc,5008/analiza;cc,5008007",
  "        Inne (Finanse / Ekonomia)" : "finanse%20ekonomia;cc,5008/inne;cc,5008003",
  "Franczyza / Własny biznes" : "franczyza%20w%C5%82asny%20biznes;cc,5009",
  "        Artykuły przemysłowe / AGD / RTV" : "franczyza%20w%C5%82asny%20biznes;cc,5009/artyku%C5%82y%20przemys%C5%82owe%20agd%20rtv;cc,5009001",
  "        Artykuły spożywcze" : "franczyza%20w%C5%82asny%20biznes;cc,5009/artyku%C5%82y%20spo%C5%BCywcze;cc,5009002",
  "        Chemia / Kosmetyki" : "franczyza%20w%C5%82asny%20biznes;cc,5009/chemia%20kosmetyki;cc,5009003",
  "        Doradztwo / Konsulting" : "franczyza%20w%C5%82asny%20biznes;cc,5009/doradztwo%20konsulting;cc,5009004",
  "        Edukacja / Szkolenia" : "franczyza%20w%C5%82asny%20biznes;cc,5009/edukacja%20szkolenia;cc,5009005",
  "        Finanse / Bankowość" : "franczyza%20w%C5%82asny%20biznes;cc,5009/finanse%20bankowo%C5%9B%C4%87;cc,5009006",
  "        Gastronomia" : "franczyza%20w%C5%82asny%20biznes;cc,5009/gastronomia;cc,5009007",
  "        Hotelarstwo / Turystyka" : "franczyza%20w%C5%82asny%20biznes;cc,5009/hotelarstwo%20turystyka;cc,5009008",
  "        IT / Telekomunikacja" : "franczyza%20w%C5%82asny%20biznes;cc,5009/it%20telekomunikacja;cc,5009009",
  "        Motoryzacja" : "franczyza%20w%C5%82asny%20biznes;cc,5009/motoryzacja;cc,5009010",
  "        Nieruchomości" : "franczyza%20w%C5%82asny%20biznes;cc,5009/nieruchomo%C5%9Bci;cc,5009011",
  "        Odzież / Dodatki / Biżuteria" : "franczyza%20w%C5%82asny%20biznes;cc,5009/odzie%C5%BC%20dodatki%20bi%C5%BCuteria;cc,5009012",
  "        Ubezpieczenia" : "franczyza%20w%C5%82asny%20biznes;cc,5009/ubezpieczenia;cc,5009013",
  "        Usługi dla klienta indywidualnego" : "franczyza%20w%C5%82asny%20biznes;cc,5009/us%C5%82ugi%20dla%20klienta%20indywidualnego;cc,5009014",
  "        Inne" : "franczyza%20w%C5%82asny%20biznes;cc,5009/inne;cc,5009015",
  "Hotelarstwo / Gastronomia / Turystyka" : "hotelarstwo%20gastronomia%20turystyka;cc,5010",
  "        Hotelarstwo" : "hotelarstwo%20gastronomia%20turystyka;cc,5010/hotelarstwo;cc,5010001",
  "        Katering / Restauracje / Gastronomia" : "hotelarstwo%20gastronomia%20turystyka;cc,5010/katering%20restauracje%20gastronomia;cc,5010002",
  "        Turystyka" : "hotelarstwo%20gastronomia%20turystyka;cc,5010/turystyka;cc,5010003",
  "Human Resources / Zasoby ludzkie" : "human%20resources%20zasoby%20ludzkie;cc,5011",
  "        BHP" : "human%20resources%20zasoby%20ludzkie;cc,5011/bhp;cc,5011001",
  "        Kadry / Wynagrodzenia" : "human%20resources%20zasoby%20ludzkie;cc,5011/kadry%20wynagrodzenia;cc,5011002",
  "        Rekrutacja / Employer Branding" : "human%20resources%20zasoby%20ludzkie;cc,5011/rekrutacja%20employer%20branding;cc,5011003",
  "        Szkolenia / Rozwój" : "human%20resources%20zasoby%20ludzkie;cc,5011/szkolenia%20rozw%C3%B3j;cc,5011004",
  "        Zarządzanie HR" : "human%20resources%20zasoby%20ludzkie;cc,5011/zarz%C4%85dzanie%20hr;cc,5011005",
  "Internet / e-Commerce / Nowe media" : "internet%20e-commerce%20nowe%20media;cc,5013",
  "        E-marketing / SEM / SEO" : "internet%20e-commerce%20nowe%20media;cc,5013/e-marketing%20sem%20seo;cc,5013001",
  "        Media społecznościowe" : "internet%20e-commerce%20nowe%20media;cc,5013/media%20spo%C5%82eczno%C5%9Bciowe;cc,5013002",
  "        Projektowanie" : "internet%20e-commerce%20nowe%20media;cc,5013/projektowanie;cc,5013003",
  "        Sprzedaż / e-Commerce" : "internet%20e-commerce%20nowe%20media;cc,5013/sprzeda%C5%BC%20e-commerce;cc,5013004",
  "        Tworzenie stron WWW / Technologie internetowe" : "internet%20e-commerce%20nowe%20media;cc,5013/tworzenie%20stron%20www%20technologie%20internetowe;cc,5013005",
  "Inżynieria" : "in%C5%BCynieria;cc,5014",
  "        TAutomatyka" : "in%C5%BCynieria;cc,5014/automatyka;cc,5014001",
  "        TElektronika / Elektryka" : "in%C5%BCynieria;cc,5014/elektronika%20elektryka;cc,5014002",
  "        TEnergetyka konwencjonalna i odnawialna" : "in%C5%BCynieria;cc,5014/energetyka%20konwencjonalna%20i%20odnawialna;cc,5014003",
  "        TMechanika" : "in%C5%BCynieria;cc,5014/mechanika;cc,5014005",
  "        TMonterzy / Serwisanci" : "in%C5%BCynieria;cc,5014/monterzy%20serwisanci;cc,5014006",
  "        TTelekomunikacja" : "in%C5%BCynieria;cc,5014/telekomunikacja;cc,5014007",
  "        TMotoryzacja" : "in%C5%BCynieria;cc,5014/motoryzacja;cc,5014008",
  "        TLotnictwo" : "in%C5%BCynieria;cc,5014/lotnictwo;cc,5014009",
  "        TProjektowanie" : "in%C5%BCynieria;cc,5014/projektowanie;cc,5014010",
  "        TKonstrukcja / Technologie" : "in%C5%BCynieria;cc,5014/konstrukcja%20technologie;cc,5014011",
  "        TInne (Inżynieria)" : "in%C5%BCynieria;cc,5014/inne;cc,5014004",
  "IT - Administracja" : "it%20-%20administracja;cc,5015",
  "        Administrowanie bazami danych i storage" : "it%20-%20administracja;cc,5015/administrowanie%20bazami%20danych%20i%20storage;cc,5015001",
  "        Administrowanie sieciami" : "it%20-%20administracja;cc,5015/administrowanie%20sieciami;cc,5015002",
  "        Administrowanie systemami" : "it%20-%20administracja;cc,5015/administrowanie%20systemami;cc,5015003",
  "        Bezpieczeństwo / Audyt" : "it%20-%20administracja;cc,5015/bezpiecze%C5%84stwo%20audyt;cc,5015004",
  "        Wdrożenia ERP" : "it%20-%20administracja;cc,5015/wdro%C5%BCenia%20erp;cc,5015005",
  "        Wsparcie techniczne / Helpdesk" : "it%20-%20administracja;cc,5015/wsparcie%20techniczne%20helpdesk;cc,5015006",
  "        Zarządzanie usługami" : "it%20-%20administracja;cc,5015/zarz%C4%85dzanie%20us%C5%82ugami;cc,5015007",
  "IT - Rozwój oprogramowania" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016",
  "        Analiza biznesowa i systemowa" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/analiza%20biznesowa%20i%20systemowa;cc,5016001",
  "        Architektura" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/architektura;cc,5016002",
  "        Programowanie" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/programowanie;cc,5016003",
  "        Testowanie" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/testowanie;cc,5016004",
  "        Zarządzanie projektem/produktem" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/zarz%C4%85dzanie%20projektemproduktem;cc,5016005",
  "        Projektowanie UX/UI" : "it%20-%20rozw%C3%B3j%20oprogramowania;cc,5016/projektowanie%20uxui;cc,5016006",
  "Kontrola jakości" : "kontrola%20jako%C5%9Bci;cc,5034",
  "        Zarządzanie jakością" : "kontrola%20jako%C5%9Bci;cc,5034/zarz%C4%85dzanie%20jako%C5%9Bci%C4%85;cc,5034001",
  "        Zapewnienie jakości" : "kontrola%20jako%C5%9Bci;cc,5034/zapewnienie%20jako%C5%9Bci;cc,5034002",
  "Łańcuch dostaw" : "%C5%82a%C5%84cuch%20dostaw;cc,5017",
  "        Logistyka / Optymalizacja" : "%C5%82a%C5%84cuch%20dostaw;cc,5017/logistyka%20optymalizacja;cc,5017001",
  "        Magazynowanie" : "%C5%82a%C5%84cuch%20dostaw;cc,5017/magazynowanie;cc,5017002",
  "        Planowanie / Prognozowanie" : "%C5%82a%C5%84cuch%20dostaw;cc,5017/planowanie%20prognozowanie;cc,5017003",
  "        Transport i zarządzanie flotą" : "%C5%82a%C5%84cuch%20dostaw;cc,5017/transport%20i%20zarz%C4%85dzanie%20flot%C4%85;cc,5017004",
  "Marketing" : "marketing;cc,5018",
  "        Badania marketingowe" : "marketing;cc,5018/badania%20marketingowe;cc,5018001",
  "        Kampanie marketingowe / Eventy" : "marketing;cc,5018/kampanie%20marketingowe%20eventy;cc,5018002",
  "        Komunikacja marketingowa" : "marketing;cc,5018/komunikacja%20marketingowa;cc,5018003",
  "        Marketing bezpośredni" : "marketing;cc,5018/marketing%20bezpo%C5%9Bredni;cc,5018004",
  "        Marketing handlowy" : "marketing;cc,5018/marketing%20handlowy;cc,5018005",
  "        Marketing internetowy i mobilny" : "marketing;cc,5018/marketing%20internetowy%20i%20mobilny;cc,5018006",
  "        Zarządzanie marką" : "marketing;cc,5018/zarz%C4%85dzanie%20mark%C4%85;cc,5018007",
  "        Zarządzanie marketingiem" : "marketing;cc,5018/zarz%C4%85dzanie%20marketingiem;cc,5018008",
  "        Zarządzanie produktem" : "marketing;cc,5018/zarz%C4%85dzanie%20produktem;cc,5018009",
  "        Inne (Marketing)" : "marketing;cc,5018/inne;cc,5018010",
  "Media / Sztuka / Rozrywka" : "media%20sztuka%20rozrywka;cc,5019",
  "        Organizacja i obsługa imprez" : "media%20sztuka%20rozrywka;cc,5019/organizacja%20i%20obs%C5%82uga%20imprez;cc,5019001",
  "        Planowanie i zakup mediów" : "media%20sztuka%20rozrywka;cc,5019/planowanie%20i%20zakup%20medi%C3%B3w;cc,5019002",
  "        Produkcja i realizacja" : "media%20sztuka%20rozrywka;cc,5019/produkcja%20i%20realizacja;cc,5019003",
  "        Redakcja / Dziennikarstwo" : "media%20sztuka%20rozrywka;cc,5019/redakcja%20dziennikarstwo;cc,5019004",
  "Nieruchomości" : "nieruchomo%C5%9Bci;cc,5020",
  "        Ekspansja / Rozwój / Zarządzanie projektem" : "nieruchomo%C5%9Bci;cc,5020/ekspansja%20rozw%C3%B3j%20zarz%C4%85dzanie%20projektem;cc,5020001",
  "        Wynajem/Wycena" : "nieruchomo%C5%9Bci;cc,5020/wynajemwycena;cc,5020002",
  "        Utrzymanie / Zarządzanie nieruchomościami" : "nieruchomo%C5%9Bci;cc,5020/utrzymanie%20zarz%C4%85dzanie%20nieruchomo%C5%9Bciami;cc,5020003",
  "Obsługa klienta" : "obs%C5%82uga%20klienta;cc,5021",
  "        Energia / Środowisko" : "obs%C5%82uga%20klienta;cc,5021/energia%20%C5%9Brodowisko;cc,5021001",
  "        Farmacja / Medycyna" : "obs%C5%82uga%20klienta;cc,5021/farmacja%20medycyna;cc,5021002",
  "        Finanse / Bankowość / Ubezpieczenia" : "obs%C5%82uga%20klienta;cc,5021/finanse%20bankowo%C5%9B%C4%87%20ubezpieczenia;cc,5021003",
  "        Inżynieria / Technika / Produkcja" : "obs%C5%82uga%20klienta;cc,5021/in%C5%BCynieria%20technika%20produkcja;cc,5021004",
  "        IT / Telekomunikacja" : "obs%C5%82uga%20klienta;cc,5021/it%20telekomunikacja;cc,5021005",
  "        Sprzedawcy" : "obs%C5%82uga%20klienta;cc,5021/sprzedawcy;cc,5021006",
  "        Marketing / Reklama / Media" : "obs%C5%82uga%20klienta;cc,5021/marketing%20reklama%20media;cc,5021007",
  "        Motoryzacja / Transport" : "obs%C5%82uga%20klienta;cc,5021/motoryzacja%20transport;cc,5021008",
  "        Turystyka / Hotelarstwo / Katering" : "obs%C5%82uga%20klienta;cc,5021/turystyka%20hotelarstwo%20katering;cc,5021009",
  "        Usługi profesjonalne" : "obs%C5%82uga%20klienta;cc,5021/us%C5%82ugi%20profesjonalne;cc,5021010",
  "Praca fizyczna" : "praca%20fizyczna;cc,5022",
  "        Kurierzy / Dostawcy" : "praca%20fizyczna;cc,5022/kurierzy%20dostawcy;cc,5022008",
  "        Pracownicy budowlani" : "praca%20fizyczna;cc,5022/pracownicy%20budowlani;cc,5022003",
  "        Pracownicy magazynowi" : "praca%20fizyczna;cc,5022/pracownicy%20magazynowi;cc,5022004",
  "        Pracownicy ochrony" : "praca%20fizyczna;cc,5022/pracownicy%20ochrony;cc,5022005",
  "        Pracownicy rolni" : "praca%20fizyczna;cc,5022/pracownicy%20rolni;cc,5022006",
  "        Pracownicy gastronomii" : "praca%20fizyczna;cc,5022/pracownicy%20gastronomii;cc,5022007",
  "        Mechanicy / Blacharze / Lakiernicy" : "praca%20fizyczna;cc,5022/mechanicy%20blacharze%20lakiernicy;cc,5022009",
  "        Monterzy / Serwisanci / Elektrycy" : "praca%20fizyczna;cc,5022/monterzy%20serwisanci%20elektrycy;cc,5022010",
  "        Kasjerzy" : "praca%20fizyczna;cc,5022/kasjerzy;cc,5022011",
  "        Pracownicy produkcji" : "praca%20fizyczna;cc,5022/pracownicy%20produkcji;cc,5022012",
  "        Fryzjer / Kosmetyczka" : "praca%20fizyczna;cc,5022/fryzjer%20kosmetyczka;cc,5022013",
  "        Obsługa hotelowa" : "praca%20fizyczna;cc,5022/obs%C5%82uga%20hotelowa;cc,5022014",
  "        Utrzymanie czystości" : "praca%20fizyczna;cc,5022/utrzymanie%20czysto%C5%9Bci;cc,5022015",
  "        Inne (Praca fizyczna)" : "praca%20fizyczna;cc,5022/inne;cc,5022001",
  "Prawo" : "prawo;cc,5023",
  "        Prawnik" : "prawo;cc,5023/prawnik;cc,5023001",
  "        Specjaliści" : "prawo;cc,5023/specjali%C5%9Bci;cc,5023002",
  "        Windykacja" : "prawo;cc,5023/windykacja;cc,5023003",
  "        Wsparcie usług prawnych" : "prawo;cc,5023/wsparcie%20us%C5%82ug%20prawnych;cc,5023004",
  "Produkcja" : "produkcja;cc,5024",
  "        Optymalizacja procesu produkcji" : "produkcja;cc,5024/optymalizacja%20procesu%20produkcji;cc,5024001",
  "        Pracownicy produkcyjni" : "produkcja;cc,5024/pracownicy%20produkcyjni;cc,5024002",
  "        Utrzymanie ruchu" : "produkcja;cc,5024/utrzymanie%20ruchu;cc,5024003",
  "        Zarządzanie produkcją" : "produkcja;cc,5024/zarz%C4%85dzanie%20produkcj%C4%85;cc,5024004",
  "Public Relations" : "public%20relations;cc,5025",
  "        Wewnętrzny PR" : "public%20relations;cc,5025/wewn%C4%99trzny%20pr;cc,5025001",
  "        Zewnętrzny PR" : "public%20relations;cc,5025/zewn%C4%99trzny%20pr;cc,5025002",
  "Reklama / Grafika / Kreacja / Fotografia" : "reklama%20grafika%20kreacja%20fotografia;cc,5026",
  "        Animacja komputerowa / Webdesign" : "reklama%20grafika%20kreacja%20fotografia;cc,5026/animacja%20komputerowa%20webdesign;cc,5026001",
  "        Grafika / Fotografia / DTP" : "reklama%20grafika%20kreacja%20fotografia;cc,5026/grafika%20fotografia%20dtp;cc,5026002",
  "        Reklama / Copywriting / Kreacja" : "reklama%20grafika%20kreacja%20fotografia;cc,5026/reklama%20copywriting%20kreacja;cc,5026003",
  "Sektor publiczny" : "sektor%20publiczny;cc,5027",
  "        Bezpieczeństwo / Porządek Publiczny" : "sektor%20publiczny;cc,5027/bezpiecze%C5%84stwo%20porz%C4%85dek%20publiczny;cc,5027001",
  "        Kontrola / Nadzór" : "sektor%20publiczny;cc,5027/kontrola%20nadz%C3%B3r;cc,5027002",
  "        Specjaliści / Urzędnicy" : "sektor%20publiczny;cc,5027/specjali%C5%9Bci%20urz%C4%99dnicy;cc,5027003",
  "        Zamówienia publiczne" : "sektor%20publiczny;cc,5027/zam%C3%B3wienia%20publiczne;cc,5027004",
  "Sprzedaż" : "sprzeda%C5%BC;cc,5028",
  "        Energia / Środowisko" : "sprzeda%C5%BC;cc,5028/energia%20%C5%9Brodowisko;cc,5028001",
  "        Farmacja / Medycyna" : "sprzeda%C5%BC;cc,5028/farmacja%20medycyna;cc,5028002",
  "        Finanse / Bankowość / Ubezpieczenia" : "sprzeda%C5%BC;cc,5028/finanse%20bankowo%C5%9B%C4%87%20ubezpieczenia;cc,5028003",
  "        Inżynieria / Technika / Produkcja" : "sprzeda%C5%BC;cc,5028/in%C5%BCynieria%20technika%20produkcja;cc,5028004",
  "        IT / Telekomunikacja" : "sprzeda%C5%BC;cc,5028/it%20telekomunikacja;cc,5028005",
  "        Marketing / Reklama / Media" : "sprzeda%C5%BC;cc,5028/marketing%20reklama%20media;cc,5028006",
  "        Merchandising" : "sprzeda%C5%BC;cc,5028/merchandising;cc,5028012",
  "        Motoryzacja / Transport" : "sprzeda%C5%BC;cc,5028/motoryzacja%20transport;cc,5028007",
  "        Nieruchomości / Budownictwo" : "sprzeda%C5%BC;cc,5028/nieruchomo%C5%9Bci%20budownictwo;cc,5028008",
  "        Sieci handlowe" : "sprzeda%C5%BC;cc,5028/sieci%20handlowe;cc,5028013",
  "        Artykuły przemysłowe / AGD / RTV" : "sprzeda%C5%BC;cc,5028/artyku%C5%82y%20przemys%C5%82owe%20agd%20rtv;cc,5028014",
  "        Rolnictwo" : "sprzeda%C5%BC;cc,5028/rolnictwo;cc,5028009",
  "        Artykuły spożywcze / Alkohol / Tytoń" : "sprzeda%C5%BC;cc,5028/artyku%C5%82y%20spo%C5%BCywcze%20alkohol%20tyto%C5%84;cc,5028015",
  "        Turystyka / Hotelarstwo / Katering" : "sprzeda%C5%BC;cc,5028/turystyka%20hotelarstwo%20katering;cc,5028010",
  "        Chemia / Kosmetyki" : "sprzeda%C5%BC;cc,5028/chemia%20kosmetyki;cc,5028016",
  "        Usługi profesjonalne" : "sprzeda%C5%BC;cc,5028/us%C5%82ugi%20profesjonalne;cc,5028011",
  "        Odzież / Dodatki / Biżuteria" : "sprzeda%C5%BC;cc,5028/odzie%C5%BC%20dodatki%20bi%C5%BCuteria;cc,5028017",
  "        Wyposażenie domu i biura" : "sprzeda%C5%BC;cc,5028/wyposa%C5%BCenie%20domu%20i%20biura;cc,5028018",
  "        Inne (Sprzedaż)" : "sprzeda%C5%BC;cc,5028/inne;cc,5028019",
  "Transport / Spedycja / Logistyka" : "transport%20spedycja%20logistyka;cc,5031",
  "        Agencje celne" : "transport%20spedycja%20logistyka;cc,5031/agencje%20celne;cc,5031001",
  "        Spedycja" : "transport%20spedycja%20logistyka;cc,5031/spedycja;cc,5031002",
  "        Usługi kurierskie" : "transport%20spedycja%20logistyka;cc,5031/us%C5%82ugi%20kurierskie;cc,5031003",
  "        Kierowcy" : "transport%20spedycja%20logistyka;cc,5031/kierowcy;cc,5031004",
  "Ubezpieczenia" : "ubezpieczenia;cc,5032",
  "        Analizy / Ryzyko / Aktuariat" : "ubezpieczenia;cc,5032/analizy%20ryzyko%20aktuariat;cc,5032001",
  "        Ubezpieczenia majątkowe" : "ubezpieczenia;cc,5032/ubezpieczenia%20maj%C4%85tkowe;cc,5032002",
  "        Ubezpieczenia na życie" : "ubezpieczenia;cc,5032/ubezpieczenia%20na%20%C5%BCycie;cc,5032003",
  "Zakupy" : "zakupy;cc,5033",
  "        Category Management" : "zakupy;cc,5033/category%20management;cc,5033001",
  "        Nieprodukcyjne / Usługi" : "zakupy;cc,5033/nieprodukcyjne%20us%C5%82ugi;cc,5033002",
  "        Produkcyjne" : "zakupy;cc,5033/produkcyjne;cc,5033003",
  "Zdrowie / Uroda / Rekreacja" : "zdrowie%20uroda%20rekreacja;cc,5035",
  "        Apteka" : "zdrowie%20uroda%20rekreacja;cc,5035/apteka;cc,5035001",
  "        Kosmetyka / Fryzjerstwo" : "zdrowie%20uroda%20rekreacja;cc,5035/kosmetyka%20fryzjerstwo;cc,5035003",
  "        Lekarze / Opieka medyczna" : "zdrowie%20uroda%20rekreacja;cc,5035/lekarze%20opieka%20medyczna;cc,5035004",
  "        Sport / Rekreacja" : "zdrowie%20uroda%20rekreacja;cc,5035/sport%20rekreacja;cc,5035005",
  "        Inne (Zdrowie / Uroda / Rekreacja)" : "zdrowie%20uroda%20rekreacja;cc,5035/inne;cc,5035002",
  "Inne" : "inne;cc,5012"
}

#This array states the predetermined options for radius distances.
radiousArr = [0,10,20,30,50,100]




#For UI Purposes, fonts
my_font = ("IBM Plex Sans", 11)
my_font2 = ("IBM Plex Sans", 20,"bold")




# This sections, sets up the GUI on Tkinter library
root = tk.Tk()
root.title("Praca.pl Bot Scraper")
root.geometry('1000x800+400+60')
#root.iconbitmap("Icon.ico")

img1 = ImageTk.PhotoImage(Image.open("Logo.png"))


#The below lines until line 570 are just UI specifications, nothing complicated.
label1 = tk.Label(root, text="Enter Job Title: ", font=my_font,pady=10)
label1.pack()
label1.place(x=100, y=80)

JobTiitle = tk.Entry(root)
JobTiitle.pack()
JobTiitle.place(x=100, y=120)
JobTiitle.insert(0, "N/A")

label2 = tk.Label(root, text="Enter Page Number: ",font=my_font,pady=10)
label2.pack()
label2.place(x=100, y=150)


PageNum = tk.Entry(root)
PageNum.pack()
PageNum.place(x=100, y=180)
PageNum.insert(0, "N/A")

label3 = tk.Label(root, text="Select Job Family: ",font=my_font,pady=10)
label3.pack()
label3.place(x=300, y=150)

# Drop-down menu options
variable_options = list(jobFam_map.keys())

# Creating a drop-down menu
JobFam = tk.StringVar(root)
JobFam.set("N/A")  # Set the default option

dropdown = ttk.Combobox(root, textvariable=JobFam, values=variable_options,width=100,height=20)
dropdown.pack()
dropdown.place(x=300, y=180)



label4 = tk.Label(root, text="Select Location: ",font=my_font,pady=10)
label4.pack()
label4.place(x=100, y=210)

Location = tk.Entry(root)
Location.pack()
Location.place(x=100, y=240)
Location.insert(0, "N/A")

label5 = tk.Label(root, text="Select Radious: ",font=my_font,pady=10)
label5.pack()
label5.place(x=100, y=270)

Radious = tk.StringVar(root)
Radious.set("N/A")

dropdown1 = ttk.Combobox(root, textvariable=Radious, values=radiousArr)
dropdown1.pack()
dropdown1.place(x=100, y=300)

label6 = tk.Label(root, text="Select FileName: ",font=my_font,pady=10)
label6.pack()
label6.place(x=100, y=330)

FileName = tk.Entry(root)
FileName.pack()
FileName.place(x=100, y=360)

button = tk.Button(root, text="Generate", command=generateDataDump,font=my_font2,foreground = 'Blue')
button.pack()
button.place(x=460, y=450)

#w = tk.Label(root, image=img1)
#w.pack()
#w.place(x=40, y=650)

#We run the main program loop to launch the UI.
root.mainloop()
