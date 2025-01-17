url_base = 'https://nvd.nist.gov/vuln/detail/'


def crawler(cve_list):
    cve_list = set(cve_list)
    print('input cve_list:', cve_list)

    import re
    '''
-    vec_re = re.compile('class="tooltipCvss2NistMetrics">\((.*)\)</span></span>  <input')
+    vec_re = re.compile('tooltipCvss3NistMetrics">CVSS:3.1/(.*)</span></span> <input')

-    title = ['AV', 'AC', 'AU', 'RC', 'E', 'Hide', 'Capacity', 'C', 'I', 'A', 'CR', 'IR', 'AR', 'RL', 'VAL']
+    title = ['AV', 'AC', 'PR', 'UI', 'S', 'C', 'I', 'A']

    '''
    vec_re_3 = re.compile('tooltipCvss3NistMetrics">CVSS:3.1/(.*)</span></span> <input')
    vec_re_2 = re.compile('class="tooltipCvss2NistMetrics">\((.*)\)</span></span>  <input')

    title = ['AV', 'AC', 'AU', 'RC', 'E', 'Hide', 'Capacity', 'C', 'I', 'A', 'CR', 'IR', 'AR', 'RL', 'VAL', 'PR', 'UI', 'S']

    res = {}

    for cve in cve_list:
        # we assume that it's a valid url.
        fetch_url = url_base + cve
        import requests
        back_text = requests.get(fetch_url).text
        back_text = back_text.replace('\t', '').replace('\n', '').replace('\r', '')

        if vec_re_2.search(back_text) is None:
            print(f'warning: cvss 2.0 {cve} callback error. maybe not found?')
        else:
            print(f'fetch done.')

        if vec_re_3.search(back_text) is None:
            print(f'warning: cvss 3.0 {cve} callback error. maybe not found?')
        else:
            print(f'fetch done.')

        if vec_re_2.search(back_text) == None:
            vector = ''
        else:
            vector = vec_re_2.search(back_text).group(1)

        if vec_re_3.search(back_text) == None:
            vector += ''
        else:
            vector += '/' + vec_re_3.search(back_text).group(1)

        print('back_res', vector)
        vec_dict = {}
        for kv in vector.split('/'):
            try:
                k, v = kv.split(':')
            except ValueError:
                continue
            if k.upper() in vec_dict:
                continue
            vec_dict[k.upper()] = v

        # print(vec_dict)
        res[cve] = [ vec_dict[k] if k in vec_dict else '?' for k in title ]

    return res

if __name__ == '__main__':
    cve_list = []

    print('please input CVE code line-by-line, terminate by Ctrl-D')
    while True:
        try:
            cve = input()
        except:
            break;
        if cve:
            cve_list.append(cve)

    res = crawler(cve_list)
    # now we need to get formated output.
    for (cve, record) in res.items():
        print(cve, ' '.join(record))
