"""Collect public event listings; never infer dates or invent records."""
import json, re, hashlib, urllib.request, urllib.parse, datetime, pathlib, unicodedata
from html import unescape
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

OUT=pathlib.Path("discoveries.json")
today=datetime.datetime.now(ZoneInfo("America/Toronto")).date().isoformat()
old=json.loads(OUT.read_text()) if OUT.exists() else {"events":[]}
sources={
 "Cirque de Boudoir":("https://www.cirquedeboudoir.com/en/",r"/en/events/[^?#]+"),
 "Luxuria":("https://www.clubluxuria.ca/evenements",r"/event-details/[^?#]+"),
 "L'Orage":("https://www.orage.club/evenements",r"/post/[^?#]+"),
 "Café Cléopâtre":("https://lepointdevente.com/lieux/le-cabaret-cafe-cleopatre",r"/(?:billets|tickets)/[^?#]+"),
 "Débasement":("https://ra.co/events/ca/montreal",r"/events/\d+"),
}
def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"TheLegendsPublicCalendar/1.0","Accept":"text/html,application/xhtml+xml"})
 with urllib.request.urlopen(req,timeout=20) as f: return BeautifulSoup(f.read(4000000),"html.parser")
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values(): yield from walk(v)
 elif isinstance(o,list):
  for v in o: yield from walk(v)
def data(soup):
 for node in soup.select('script[type="application/ld+json"]'):
  try: yield from walk(json.loads(node.string or node.get_text()))
  except (ValueError,TypeError): continue
def clean(v): return ' '.join(str(v or '').split())
def dateok(d):
 try: return datetime.date.fromisoformat(d).isoformat()>=today
 except (ValueError,TypeError): return False
def make(org,title,date,time,place,url):
 if not title or not dateok(date): return None
 return dict(id="web:"+hashlib.sha256((org+"|"+date+"|"+norm(title)).encode()).hexdigest()[:24],organizer=org,title=title,date=date,time=time,place=place,url=url,description="Annonce publique : consulter la source pour les détails.",status="discovered",visibility="group",poster_url="",created_by="web")
def parse(soup,org,url):
 for o in data(soup):
  ty=o.get("@type",[])
  if not any(str(t).endswith("Event") for t in ([ty] if isinstance(ty,str) else ty)): continue
  start=str(o.get("startDate","")); title=clean(o.get("name")); loc=o.get("location",{});loc=loc[0] if isinstance(loc,list) and loc else loc
  if isinstance(loc,dict):
   address=loc.get("address",""); address=clean(" ".join(str(address.get(k,"")) for k in ("addressLocality","addressRegion","addressCountry"))) if isinstance(address,dict) else clean(address)
   place=clean(loc.get("name"))+" "+address
  else: place=clean(loc)
  text=norm(title+" "+place)
  if org=="Débasement" and "debasement" not in text: continue
  if org=="Café Cléopâtre" and "cleopatr" not in text: continue
  if org in ("Cirque de Boudoir","Débasement","Café Cléopâtre") and not any(k in text for k in ("montreal","theatre paradoxe","cabaret berlin","cleopatr")): continue
  if str(o.get("eventStatus","")).endswith(("EventCancelled","EventPostponed")): continue
  e=make(org,title,start[:10],start[11:16] if "T" in start else "",place.strip() or "Montréal",url)
  if e: yield e
 # Explicit dates on the two editorial sites, not publication dates.
 if org=="Cirque de Boudoir":
  h=soup.find("h1"); page=clean(soup.get_text(" ",strip=True)); match=re.search(r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\.(\d{1,2})\.(20\d{2})\s*:\s*(\d\d:\d\d)\s*//\s*(.{1,120}?)\bMontreal\b",page,re.I)
  if h and match:
   mon,day,yr,tm,loc=match.groups(); date=f"{yr}-{['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'].index(mon.upper())+1:02d}-{int(day):02d}"
   e=make(org,clean(h.get_text()),date,tm,clean(loc)+" Montréal",url)
   if e: yield e
 if org=="L'Orage" and "/post/" in url:
  h=soup.find("h1"); sub=soup.find("h2")
  if h and sub:
   m=re.search(r"\b(\d{1,2})(?:er)?\s+([a-z]+)\.?\s+(20\d{2})\b",norm(h.get_text()))
   months={"janvier":1,"jan":1,"fevrier":2,"fev":2,"mars":3,"avril":4,"avr":4,"mai":5,"juin":6,"juillet":7,"juil":7,"aout":8,"septembre":9,"sept":9,"octobre":10,"oct":10,"novembre":11,"nov":11,"decembre":12,"dec":12}
   if m and m[2] in months:
    e=make(org,clean(sub.get_text()),f"{m[3]}-{months[m[2]]:02d}-{int(m[1]):02d}","","L'Orage, Montréal",url)
    if e: yield e
events={ (e["organizer"],e["date"],norm(e["title"])):e for e in old.get("events",[]) if dateok(e["date"])}
status={}
for org,(url,pattern) in sources.items():
 count=0; errors=0
 try:
  soup=fetch(url)
  links=list(dict.fromkeys(urllib.parse.urljoin(url,a["href"]) for a in soup.select("a[href]") if re.search(pattern,a["href"]) and urllib.parse.urlparse(urllib.parse.urljoin(url,a["href"])).netloc==urllib.parse.urlparse(url).netloc))
  if org=="Débasement": links=[urllib.parse.urljoin(url,a["href"]) for a in soup.select("a[href]") if "debasement" in norm(a.get_text(" ",strip=True)) and re.search(pattern,a["href"])]
  for link in [url]+list(dict.fromkeys(links))[:35]:
   try:
    page=soup if link==url else fetch(link)
    for e in parse(page,org,link):
     key=(e["organizer"],e["date"],norm(e["title"]))
     if key not in events and not any(x["organizer"]==e["organizer"] and x["date"]==e["date"] and x["url"]==e["url"] for x in events.values()):
      events[key]=e; count+=1
   except Exception as exc: errors+=1; print(org,link,str(exc))
  status[org]={"new":count,"pages_failed":errors,"state":"partial" if errors else "checked","links_found":len(links)}
 except Exception as exc: status[org]={"state":"unavailable","error":str(exc)[:200]}
 print(org,status[org])
OUT.write_text(json.dumps({"updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"sources":status,"events":sorted(events.values(),key=lambda e:(e["date"],e["title"]))},ensure_ascii=False,indent=2)+"\n")
