#!/usr/bin/env python
#coding: utf-8
import sys, os, csv, datetime, time, urllib, urllib2, socket
import simplejson as json
from uniparser import UniParser
# Init socket timeout to avoid connection break from api.skyur.ru
socket.setdefaulttimeout(15)

FILES_R = ['amb_r.csv', 'ambc1_r.csv', 'ambc2_r.csv']
AMB_FILENAME = 'allamb.csv'
GENDER_URL = "http://apibeta.skyur.ru/names/parse/?%s"
CLASSIFY_URL = "http://apibeta.skyur.ru/names/classify/?%s"


def get_gender(name):
    """Gets gender data for name specified"""
    params = urllib.urlencode({'text' : name})
    url = GENDER_URL % params
    try:
        f = urllib2.urlopen(url.encode('utf8'))
    except:
        f = urllib2.urlopen(url.encode('utf8'))
    data = f.read()
    f.close()
    return json.loads(data)

def get_nameinfo(sname, fname, mname):
    """Gets name information by surname, first name and middle name"""
    params = urllib.urlencode({'fn' : fname.encode('utf8'), 'mn' : mname.encode('utf8'), 'sn' : sname.encode('utf8')})
    url = CLASSIFY_URL % params
    try:
        f = urllib2.urlopen(url.encode('utf8'))
    except:
        f = urllib2.urlopen(url.encode('utf8'))
    data = f.read()
    f.close()
    return json.loads(data)
    

def parse(fromfile, tofile):
    """Parses ambassodors filename"""
    names = ['name', 'birthday', 'department', 'depjoindate', 'position', 'rank', 'rankdate']
    writer = csv.writer(open(tofile, 'w'), delimiter="\t", quotechar='"')
    reader = csv.reader(open(fromfile, 'r'), delimiter="\t", quotechar='"')
    writer.writerow(names)
    i = 0
    for row in reader:
        i += 1
        if i == 1: continue        
        name, birthday = row[0].rsplit(' ', 1)
        try:
            bd = datetime.datetime.strptime(birthday, '%d.%m.%Y')
        except ValueError:
            name = name + ' ' + birthday
            birthday = "None"

        if len(row[1]) == 0:
            department = "None"
            depjoindate = "None"
        else:
            department, depjoindate = row[1].rsplit(' ', 1)
        rank, rankdate = row[3].rsplit(' ', 1)
        writer.writerow([name, birthday, department, depjoindate, row[2], rank, rankdate])
        print name
    

def calc_datediff(d1, d2):
    """Calculates age difference"""
    years = d1.year - d2.year
    if d1.month < d2.month:
        years -=1
    elif d1.month == d2.month and d1.day < d2.day: 
        years -=1
    return years      


def average(values):
    """Average values"""
    return sum(values, 0.0) / len(values)

def measure_age():
    """Measures age"""
    positions = {}
    ranks = {}
    v_old = []
    f = AMB_FILENAME
    now = datetime.datetime.now()
    reader = csv.reader(open(f, 'r'), delimiter="\t", quotechar='"')
    i = 0
    ally = []
    for row in reader:
        i += 1
        if i == 1: continue
        if len(row[1]) == 0:
            continue
        dater = now
        d = datetime.datetime.strptime(row[7], '%d.%m.%Y')
        years = calc_datediff(now, d)
        ally.append(years)
        pos = row[10]            
        v = positions.get(pos, None)
        if v is None:
            positions[pos] = [years,]
        else:
            positions[pos].append(years)

        rank = row[11]            
        v = ranks.get(rank, None)
        if v is None:
            ranks[rank] = [years,]
        else:
            ranks[rank].append(years)
        
        if years > 70:
            v_old.append(row)
    for k, v in positions.items():
        print '\t'.join([k, str(average(v)), str(len(v))])
    for k, v in ranks.items():
        print '\t'.join([k, str(average(v)), str(len(v))])
#    print "Very old", len(v_old)
#    for old in v_old:
#        print old[0], old[1], old[2], old[4]


def enrich_data(filename=AMB_FILENAME):
    now = datetime.datetime.now()
    names = ['name', 'surname', 'firstname', 'midname', 'gender', 'ethnics', 'age', 'birthday', 'department', 'depjoindate', 'position', 'rank', 'rankdate', 'rankage']
    writer = csv.writer(open(filename, 'w'), delimiter="\t", quotechar='"')
    writer.writerow(names)    
    for f in FILES_R:
        reader = csv.reader(open(f, 'r'), delimiter="\t", quotechar='"')
        i = 0
        ally = []
        for row in reader:
            i += 1
            if i == 1: continue
#            if len(row[1]) == 0:
#                continue
            g = get_gender(row[0])
            if g['parsed']:
                if not g.has_key('mn'): g['mn'] = ''
                info = get_nameinfo(g['sn'], g['fn'], g['mn'])
                ethnics = ','.join(info['ethnics'])
                gender = g['gender']
            else:
                gender = ""
                ethnics = ""
                g['sn'] = ''
                g['mn'] = ''
                g['fn'] = ''
            print row[1], '|', row[6]
            try:
                bd = datetime.datetime.strptime(row[1], '%d.%m.%Y')
            except ValueError:
                bd = None
            try:
                rd = datetime.datetime.strptime(row[6], '%d.%m.%Y')
            except ValueError:
                rd = None
            age = calc_datediff(now, bd) if bd is not None else 0
            rankyears = calc_datediff(rd, bd) if rd is not None and bd is not None else 0
            nrow = [row[0], g['sn'].encode('utf8'), g['fn'].encode('utf8'), g['mn'].encode('utf8'), gender, ethnics, age, row[1], row[2], row[3], row[4], row[5], row[6], rankyears]
            writer.writerow(nrow)
            print f, i, row[0]


def store_page(url, filename):
    parser = UniParser()
    table = parser.parseTables(url, "//table[@id='diptbl']")
    if len(table) == 0:
        table = parser.parseTables(url, "//table[@class='diptbl']")
    writer = csv.writer(open(filename, 'w'), delimiter="\t")
    for row in table:
        writer.writerow(row)
#    print table


def download_data():
    store_page("http://www.mid.ru/bdomp/personnel-matters.nsf/info/06.015.01", "amb.csv")
    store_page("http://www.mid.ru/bdomp/personnel-matters.nsf/info/06.015.02", "ambc1.csv")
    store_page("http://www.mid.ru/bdomp/personnel-matters.nsf/info/06.015.03", "ambc2.csv")


def process_all():
    download_data()
    parse("amb.csv", "amb_r.csv")
    parse("ambc1.csv", "ambc1_r.csv")
    parse("ambc2.csv", "ambc2_r.csv")
    enrich_data()


if __name__ == "__main__":
    process_all()
#    enrich_data()
#    measure_age()
#    parse(sys.argv[1], sys.argv[2])