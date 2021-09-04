import pulp as p
import os

#input handling
num_slice = int(input()) 
num_work = int(input())
work_list = []
weight_ls = []
num_op_ls = []
up_bound = 0
for i in range(num_work):  
  num_op = int(input())
  weight = float(input())
  op_dict = {}
  num_op_ls.append(num_op)
  for j in range(num_op): 
    para_dict = {}
    input_ = input().split()
    slice_need = int(input_[0])
    duration = int(input_[1])
    num_dep = int(input_[2])
    up_bound+= duration * slice_need
    para_dict["slice_need"] = slice_need
    para_dict["duration"] = duration
    para_dict["num_dep"] = num_dep
    para_dict["dep"] = []
    for k in range(3,num_dep + 3):
      dep = int(input_[k])
      para_dict["dep"].append(dep)
    op_dict[j] = para_dict
  work_list.append(op_dict)
  weight_ls.append(weight)

problem = p.LpProblem("NASA", p.LpMinimize)

# Set start, end variable
S_ls = []
E_ls = []
E_max_ls=[]
E_max = p.LpVariable("E1Max", 0, up_bound, p.LpInteger)
for i in range(num_work):
  op_S_ls = {}
  op_E_ls = {}
  MAX = p.LpVariable("EMax"+"_"+str(i+1), 0, up_bound, p.LpInteger)
  E_max_ls.append(MAX)
  for key in work_list[i].keys():
    s_ls = []
    e_ls = []
    for j in range(work_list[i][key]["slice_need"]):
      S = p.LpVariable("S"+str(i+1)+"_"+str(key)+"_"+str(j+1), 0, up_bound, p.LpInteger)
      E = p.LpVariable("E"+str(i+1)+"_"+str(key)+"_"+str(j+1), 0, up_bound, p.LpInteger)
      s_ls.append(S)
      e_ls.append(E)
    op_S_ls[key] = s_ls
    op_E_ls[key] = e_ls
  S_ls.append(op_S_ls)
  E_ls.append(op_E_ls)

# target to minimize
target = E_max
for i in range(num_work):
  target+=weight_ls[i]*E_max_ls[i]
problem+=target

# Start, end point and time interval being occupied
Sp_ls =[]
Ep_ls = []
Num_ls=[]
for i in range(num_work):
  op_Sp_ls = {}
  op_Ep_ls = {}
  op_Num_ls = {}
  for key in work_list[i].keys():
    sp_ls = []
    ep_ls = []
    num_ls = []
    for j in range(work_list[i][key]["slice_need"]):
      Sp = p.LpVariable.dicts("WorkSP"+str(i+1)+"_"+str(key)+"_"+str(j+1), list(range(up_bound)), cat="Binary")
      Ep = p.LpVariable.dicts("WorkEP"+str(i+1)+"_"+str(key)+"_"+str(j+1), list(range(up_bound)), cat="Binary")
      Num = p.LpVariable.dicts("WorkNum"+str(i+1)+"_"+str(key)+"_"+str(j+1), list(range(up_bound)), cat="Binary")
      sp_ls.append(Sp)
      ep_ls.append(Ep)
      num_ls.append(Num)
    op_Sp_ls[key] = sp_ls
    op_Ep_ls[key] = ep_ls
    op_Num_ls[key] = num_ls
  Sp_ls.append(op_Sp_ls)
  Ep_ls.append(op_Ep_ls)
  Num_ls.append(op_Num_ls)

# Relationship between start and end
for i in range(num_work):
  for key in work_list[i].keys():
    for j in range(work_list[i][key]["slice_need"]):
      problem += (S_ls[i][key][j]+ work_list[i][key]["duration"] == E_ls[i][key][j])
#Relationship of dependency
for i in range(num_work):
  for key in work_list[i].keys():
    for j in range(work_list[i][key]["slice_need"]):
      for k in range(len(work_list[i][key]["dep"])):
        dep = work_list[i][key]["dep"][k]
        for r in range(work_list[i][dep-1]["slice_need"]):
          problem += (S_ls[i][key][j] >= E_ls[i][dep-1][r])
    for j in range(work_list[i][key]["slice_need"]-1):
      problem += (S_ls[i][key][j] == S_ls[i][key][j+1])
# Relationship between E_i_max and others
for i in range(num_work):
  for key in work_list[i].keys():
    for j in range(work_list[i][key]["slice_need"]):
      problem += (E_max_ls[i]>=E_ls[i][key][j])
  problem += (E_max >= E_max_ls[i])

# Constraints of interval
for i in range(num_work):
  for key in work_list[i].keys():
    for j in range(work_list[i][key]["slice_need"]):
      problem += p.lpSum([Sp_ls[i][key][j][k] * k for k in range(up_bound)]) == S_ls[i][key][j]
      problem += p.lpSum([Ep_ls[i][key][j][k] * k for k in range(up_bound)]) == E_ls[i][key][j]
      problem += p.lpSum([Sp_ls[i][key][j][k] for k in range(up_bound)]) == 1 
      problem += p.lpSum([Ep_ls[i][key][j][k] for k in range(up_bound)]) == 1 
      problem += p.lpSum([Num_ls[i][key][j][k] for k in range(up_bound)]) == work_list[i][key]["duration"] 
# Relationship between interval and start/end point

for k in range(1, up_bound):
  for i in range(num_work):
    for key in work_list[i].keys():
      for j in range(work_list[i][key]["slice_need"]):
        problem += (Num_ls[i][key][j][k] + (1 - Sp_ls[i][key][j][k]) + Ep_ls[i][key][j][k] == Num_ls[i][key][j][k - 1] + 1)


for k in range(up_bound):
  target = 0
  for i in range(num_work):
    for key in work_list[i].keys():
      for j in range(work_list[i][key]["slice_need"]):
        target += Num_ls[i][key][j][k]
  problem+=(target<=num_slice)

problem.solve()
for i in range(num_work):
  for k in range(num_op_ls[i]):
    for j in range(work_list[i][k]["slice_need"]):
        print(p.value(S_ls[i][k][j]))
        print(p.value(E_ls[i][k][j]))
print(p.value(E_max))
print(p.value(problem.objective))
