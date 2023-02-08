prob_comp_list = []
prob_topo = []

def prob_get_res():
	# print('prob_comp_list', prob_comp_list)
	# print('prob_topo', prob_topo)
	cve_set = set()
	print('-------------------------------dump dev into-------------------------------')
	for cmp in prob_comp_list:
		id = cmp.getID()
		dev = cmp.getName()
		vli = cmp.getVulnerabilityList()
		for v in vli:
			print(dev, v.getCVE())
			cve_set.add(v.getCVE())
		pass

	print('-------------------------------dump cve list-------------------------------')
	for cve in cve_set:
		print(cve)

	print('-------------------------------dump topo-------------------------------')
	# print(prob_topo)
	prob_topo_set = set(prob_topo)
	for (a, b) in prob_topo_set:
		print(a, b)
