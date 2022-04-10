#Import thư viện
import requests
import re
import json
from bs4 import BeautifulSoup
import csv
import concurrent.futures as cf
#Link web

url = "https://careerbuilder.com"
url_base = "https://www.careerbuilder.com/jobs?cb_workhome=true&keywords=&page_number="
#Cào dữ liệu
#Các hàm xử lý chuỗi

#làm sạch string, ex: "\n\t remote job"  return "remove job"
def clean(text):
  return re.sub('\s+', '', text)
#covert số str sang int, ex: "lương 25,9879$" return 259879
def get_num(s):
  lst = re.findall('\d+', s)
  string = ''.join(lst)
  return int(string)
#Hàm chuyển html sang soup

def get_soup(url):
  req = requests.get(url)
  return BeautifulSoup(req.text,"lxml")
#Các hàm tạo dict and list

#đếm số lượng công việc (số lượng ghi trên web)
def get_count_job(soup):
  return soup.select_one('#job-count').text
url_first = "https://www.careerbuilder.com/jobs?cb_workhome=true&keywords=&page_number=1"
soup_first =get_soup(url_first)
json_data = {
    'Remote job': 'Remote',
    'Number of posts': get_num(get_count_job(soup_first)),
    'Job_info':[]
}
def get_job_info():
  return  {
      'Number of applying': None,
      'Title': '',
      'Description': {
          'Recommended Skills':None,
          'Qualifications':None
          },
      'Type': None,
      'Level of positions': None,
      'Compensation offered': None,
      'Location': None,
      'Business field': None 
  }
#Các hàm lọc

def get_href(link):
  #lấy link từ thẻ <a>
  return link.get("href")
def get_link():
  lst_linkjob = list()
  def c_get_link(link):
    return url + get_href(link)
   #lấy demo 10*25 job
  for i in range(1,11):
  # for i in range(1,(get_num(get_count_job(soup_first)))//25+2): #khi làm thực tế thì lấy cái này
    soup =get_soup(url_base+str(i))
    job_link = soup.select("#jobs_collection a.data-results-content")
    with cf.ThreadPoolExecutor() as exe:
      lst_linkjob = list(lst_linkjob + list(exe.map(c_get_link, job_link)))
  return list(set(lst_linkjob))
def get_header(soup):
  #lấy title, location,type,Compensation offered,Business field, Recommended Skills
  tmp = soup.select_one('div.data-display-header_info-content')
  def get_text(span):
    return clean(span.text)
  lst =list()
  try:
    lst= list(map(get_text,tmp.select('div.data-details span')))
  except:
    #một số web sẽ không đây đủ thông tin cho cả ba loại
    lst = [None,None,None]
  try:
    lst.append(clean(tmp.select_one('h2').text))
  except:
    lst.append(None)
  try:
    lst.append(clean(tmp.select_one('#cb-salcom-info').text))
  except:
    lst.append(None)
  return lst
def get_disp(soup):
  #lấy  Qualifications
  soup=soup.select_one('#jdp_description div .col-mobile-full')
  try:
    lst = soup.find_all(text=re.compile('ualifications'))
  except:
    return None
  disp = []
  for i in lst:
    if i.parent.find_next_sibling('ul'):
      disp.append(clean(i.parent.find_next_sibling('ul').text))
    elif  i.parent.parent.find_next_sibling('ul'):
      disp.append( clean(i.parent.parent.find_next_sibling('ul').text))
    else:
      return None
  return disp
#Main crawl

def main_crawl(link):
  # link =lst_linkjob[3]
  job_info = get_job_info()
  sc = get_soup(link)
  header = get_header(sc)
  if len(header) == 5:
    job_info['Business field'],job_info['Location'],job_info['Type'],job_info['Title'] ,job_info['Compensation offered'] = header
  elif len(header) == 4:
    job_info['Business field'],job_info['Type'],job_info['Title'] ,job_info['Compensation offered'] = header
  job_info['Description']['Recommended Skills'] = [clean(rcm.text) for rcm in sc.select('div.col.big.col-mobile-full > div.bloc ul li')]
  # print(sc.select_one('div.col.big.col-mobile-full > div.bloc ul').text)
  job_info['Description']['Qualifications'] = get_disp(sc)
  return job_info
#lấy link cho vào list lst_linkjob
lst_linkjob= get_link()
#số lượng linkjob
len(lst_linkjob)
250
with cf.ThreadPoolExecutor() as exe:
    json_data['Job_info'] = list(exe.map(main_crawl, lst_linkjob))
#Chuyển data sang file Json

#to json
json.dump( json_data['Job_info'],open('careerbuilder.json','w'),indent=4)


#to csv
csv_file = "careerbuilder.csv"
csv_columns = get_job_info()
try:
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in json_data['Job_info']:
            writer.writerow(data)
except IOError:
    print("I/O error")