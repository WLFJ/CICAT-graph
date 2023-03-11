'''
output: generate new graph with pre-prob and post-prob.

input: assets-topo, cve-list.

algorithm:
	1. make device topo.(attack-graph like).
	2. calc single node (inother word, device) attack prob (p_{inner}).
		2.1 iterate all cve and get score, choose the maximume one.
	3. calc post-prob
		3.1 accumulate all related nodes point to current node, multiply there p_{inner}.
		3.2 multiply current node's p.
'''

'''
def cve_impact(cve):
	cr = ?
	c = ?
	ir = ?
	i = ?
	ar = ?
	a = ?
	ic = cr * c
	ii = ir * i
	ia = ar * a
	impact = (ic + ii + ia) / 3.0 * rl * val
'''


assets = {}

def load_assets(ws):
	is_title = True
	for (c0, c1) in ws.rows:
		if is_title:
			is_title = False
			continue
		k, v = c0.value, c1.value
		if k in assets:
			assets[k].append(v)
		else:
			assets[k] = [v]


graph = {}

def load_topo(ws):
	is_title = True
	for (c0, c1) in ws.rows:
		if is_title:
			is_title = False
			continue
		a, b = c0.value, c1.value
		if a in graph:
			graph[a].append(b)
		else:
			graph[a] = [b]


cves = {}

def load_cve(ws):
	is_title = True
	for (k, av, ac, au, rc, e, hide, capacity, c, i, a, cr, ir, ar, rl, val, pr, ui, s) in ws.rows:
		if is_title:
			is_title = False
			continue
		(k, av, ac, au, rc, e, hide, capacity, c, i, a, cr, ir, ar, rl, val, pr, ui, s) = (k.value, av.value, ac.value, au.value, rc.value, e.value, hide.value, capacity.value, c.value, i.value, a.value, cr.value, ir.value, ar.value, rl.value, val.value, pr.value, ui.value, s.value)
		
		
		cves[k] = {
			'av': av,
			'ac': ac,
			'au': au,
			'rc': rc,
			'e': e,
			'hide': hide,
			'capacity': capacity,
			'c': c,
			'i': i,
			'a': a,
			'cr': cr,
			'ir': ir,
			'ar': ar,
			'rl': rl,
			'val': val,
            'pr': pr,
            'ui': ui,
            's': s,
		}
	

tai = {}

def load_tai(ws):
	is_title = True
	last_0 = None
	for (c0, c1, c2) in ws.rows:
		if is_title:
			is_title = False
			continue
		
		v0, v1, v2 = c0.value, c1.value, c2.value
		
		if v0 == None:
			v0 = last_0
		else:
			last_0 = v0
		
		tai[(v0.upper(), v1)] = float(v2)

	
hci = {}

def load_hci(ws):
	skip_cnt = 2
	for (c0, c1, c2, c3) in ws.rows:
		if skip_cnt:
			skip_cnt -= 1
			continue
		v0, v1, v2, v3 = c0.value, c1.value, c2.value, c3.value		
		hci[(v0, 'C')] = v1
		hci[(v0, 'P')] = v2
		hci[(v0, 'N')] = v3

	
def clean_cve():
	for k in cves.keys():
		for t, v in cves[k].items():
			tt = t.upper()
			if v == '?':
				v = 'ND'
			if tt in ['AV', 'AC', 'AU', 'RC', 'E', 'C', 'I', 'A', 'CR', 'IR', 'AR', 'RL']:
				# update in tai
				kk = (tt, v)
				if kk in tai:
					cves[k][t] = tai[kk]
				else:
					print(f'[clean_cve]: error: cve: {k}\'s {kk} filed not defined, will assign into 1 by defualt.')
					cves[k][t] = 1.0
					
				pass
			elif tt in ['HIDE']:
				# update in hci
				kk = (cves[k]['i'], cves[k]['a'])
				if kk in hci:
					cves[k][t] = hci[kk]
				else:
					print(f'[clean_cve]: error: cve: {k}\'s {tt}:{kk} filed not defined, will assign into 1 by defualt.')
					cves[k][t] = 1.0
				pass
			elif tt in ['VAL', 'CAPACITY']:
				if v == 'ND':
					print(f'[clean_cve]: error: cve: {k}\'s {t} filed not defined, will assign into 1 by defualt.')
					cves[k][t] = 1.0
				else:
					cves[k][t] = float(cves[k][t])
			else:
				print('[clean_cve]: error: not found field: ' + t)

def p_innter(cve):
	# how to map val?
	res = 1.0
	for k, v in cve.items():
		if k in ['av', 'ac', 'au']:
			res *= v
	res *= 0.85 # UI
	return res


if __name__ == '__main__':
	from openpyxl import load_workbook
	wb = load_workbook('SCENARIO-new-fake.xlsx')

	# load related data into runtime
	load_assets(wb.worksheets[0])
	load_topo(wb.worksheets[1])
	load_cve(wb.worksheets[2])
	load_tai(wb.worksheets[3])
	load_hci(wb.worksheets[4])
	load_tai(wb.worksheets[5])
	wb.close()

	clean_cve()

	print('[info]: load finished. start calc...')
	n_pi = {}
	for k, v in assets.items():
		# calc each cve, only save the maximum one.
		max_cve_p_inner = -1.0
		for cve_id in v:
			cve_res = p_innter(cves[cve_id])
			max_cve_p_inner = max(max_cve_p_inner, cve_res)

		n_pi[k] = max_cve_p_inner

	print('[info]: p_inner calc finished.')


	indeg = {}
	for k, v in graph.items():
		for vv in v:
			if vv in indeg:
				indeg[vv].append(k)
			else:
				indeg[vv] = [k]

	# print(indeg)

	changed = True
	ps = {}
	while changed:
		changed = False
		for k in set(indeg.keys()) | set(graph.keys()):
			# print('----------current', k)
			if k in ps:
				# print('abort-has-res', k)
				continue
			else:
				if k not in indeg:
					ps[k] = 1.0
					changed = True		
				else:
					if len(indeg[k]) == 1:
						if indeg[k][0] in ps:
							if k not in n_pi:
								# print('err: ', k)
								pass
							pi = n_pi[k] if k in n_pi else 1.0
							ps[k] = ps[indeg[k][0]] * pi
							# print('update', k)
							changed = True
						else:
							# print('abort-single', k)
							continue
					else:
						res = 1.0
						for sub in indeg[k]:
							if sub in ps:
								if k not in n_pi:
									# print('err: ', k)
									pass
								pi = n_pi[k] if k in n_pi else 1.0
								res = res * (1 - ps[sub] * pi)
							else:
								res = 0
								break
						if res == 0:
							# print('abort-iter', k)
							continue
						else:
							ps[k] = 1 - res
							# print('update', k)
							changed = True
						

	print('[info]: calc finished.')

	'''
	for k in graph:
		pi = n_pi[k] if k in n_pi else '--'
		p = ps[k] if k in ps else '--'
		print(k, pi, p)
	'''

	print('[info]: start graph gen.')

	client_id_dict = dict()

	dot_node_list = []
	dot_edges = []

	'''
	Get client id, if not contained, auto new one.
	'''
	def getId(client, aced_client_name=''):
		_client = client

		if _client not in client_id_dict:
			client_id = len(client_id_dict) + 1 # Start from 1.
			client_id_dict[_client] = client_id
			# here we also need to add number on it.
			pi = round(n_pi[_client],3) if _client in n_pi else 1.0
			p = round(ps[_client],3) if _client in ps else '--'
			dot_node_list.append(f'  {client_id} [label="{client}\\np_inner={pi}, p={p}", shape=ellipse];')

		return client_id_dict[_client]

	for (k, v) in graph.items():
		k_id = getId(k)
		for vv in v:
			v_id = getId(vv)
			dot_edges.append(f'  {k_id} -> {v_id};')

	dot_edges_set = set(dot_edges)
	res_dag = 'digraph G {\n' + '\n'.join(dot_node_list) + '\n' + '\n'.join(dot_edges_set) + '\n}'
	print(res_dag)

	with open('RESULT.dot', 'w') as f:
		f.write(res_dag)

	from os import system as shell
	shell(f'dot -Tpdf RESULT.dot > RESULT.pdf')
	print('[info]: file save to RESULT.dot and RESULT.pdf')
