'''
convert row-based cve record into column based record.

and also claw related cve info and dump them into file.
'''

file = 'assets-cve.xlsx'

from openpyxl import load_workbook
wb = load_workbook(file)
ws = wb.active

CVE_RE = 'CVE-[0-9]{4}-[0-9]{4}'
import re
cve_r_c = re.compile(CVE_RE)

db = {}
for row in ws:
    asset = row[0].value
    db[asset] = []
    for i in range(1, len(row)):
        cve = row[i]
        if cve.value == None:
            break
        val = cve.value
        val = cve_r_c.match(val).group()
        db[asset].append(val)

# dump asset cve into file
cve_rec_li = []
cve_set = set()
for a, c in db.items():
    print("CT"+a, ','.join(c))
    for cve in c:
        cve_rec_li.append(f'{a} {cve}')
        cve_set.add(cve)


with open('cve-list.txt', 'w') as f:
    f.write('\n'.join(cve_rec_li) + '\n')

# claw cve info and dump them into file.
from get_cve_full_info import crawler
res = crawler(cve_set)
cve_info_res_list = []
for (cve, record) in res.items():
    cve_info_res_list.append(cve + ' ' + ' '.join(record))

with open('cve-info.txt', 'w') as f:
    f.write('\n'.join(cve_info_res_list) + '\n')

