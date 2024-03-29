# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 12:18:38 2020

@author: zohre
"""


import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import Normalizer
from sklearn import decomposition, datasets, model_selection, preprocessing, metrics

from numpy import *
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import Normalizer
import Graph_Sampling 
from networkx.algorithms.approximation import min_weighted_vertex_cover
import time
from networkx.algorithms import has_path
#from matrix_completion import svt_solve, calc_unobserved_rmse
import scipy.sparse as sps
import itertools
import pandas as pds
import pickle
import math
import random
import numpy as np
import copy
import seaborn as sns
import networkx as nx

from sklearn.decomposition import NMF
## set input parameters 
query_budget=500000000
rank=16
depth_limit_search=3
source_node=5
num_traverse=2
bfs_list=[]
dfs_list=[]
sources=[5,3406,3,10,16]
backbone=False
jump_prob=.2
burning_prob=.4
##### input dataset
time_start = time.perf_counter()


g = nx.read_edgelist("./Documents/notes/code_reachability/Reachability_Learning/dataset/web-Google.txt", create_using= nx.DiGraph(),nodetype=int)

num_edges=g.number_of_edges()
num_nodes=g.number_of_nodes()

print("number of nodes: {}".format(num_nodes) )

print("number of edges: {}".format(num_edges) )
##search based on the predecessors

pred=nx.predecessor(g,source=5)
def select_pred(neigbours):
    max_pred=0
    for i in neigbours:
        for j in neigbours:
            if len(pred[i])> len(pred[j]):
                max_pred=i
            else:
                max_pred=j
    print(max_pred)        
    return max_pred                 
def sorted_pred(neigbours):
   
    pred_neigbour=[len(pred[x]) for x in neigbours]
    #sorted_pred=pred_neigbour.sort(key=len) 
    sorted_pred=[x for _,x in sorted(zip(pred_neigbour,neigbours))]
     
    print(sorted_pred)
           
    return sorted_pred       

def dfs_pred(visited, graph, node,query_budget ):
    if node not in visited and len(visited)<query_budget:
        print (node)
        visited.add(node)
        neighbour=list(g.neighbors(node))
        if not neighbour:
            print("not neigbour")
            random_node = random.randint(1,num_nodes)
            dfs_pred(visited, graph, random_node,query_budget)
        else:
            print(neighbour)
            selected=sorted_pred(neighbour)
            for s in selected:
                dfs_pred(visited, graph, s,query_budget)



def dfs( start):
    visited, stack = set(), [start]
    while stack and len(visited)<query_budget:
        print(len(visited))
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            
            unvisited=set(g.nodes) - visited
            #removable=[x for x in unvisited if x not in list(pred.keys())]
            
            selected=sorted_pred(unvisited)
           
            stack.extend(selected)
    return visited


dfs_predecessor=dfs(5)

#to verify high degree nodes
#high_degree=sorted(g.degree, key=lambda x: x[1], reverse=True)
#selected=high_degree[:4000]


## dfs (multiple DFS with depth)
dfs_depth=sorted(list(nx.dfs_tree(g, source=source_node, depth_limit=3).edges()))


## bfs (multiple BFS with depth)
bfs_depth=sorted(list(nx.bfs_tree(g, source=source_node, depth_limit=depth_limit_search).edges()))




## extract min vertex cover
reach_minVertex=sps.lil_matrix((num_nodes, num_nodes), dtype=np.int8)
            
min_vertex=min_weighted_vertex_cover(g)
count=0
while count<query_budget:
    i=random.choice(list(min_vertex))
    j=random.choice(list(min_vertex))
    if(has_path(g,i,j)) and i!=j:
            reach_minVertex[i,j]=1
            count=count+1
           
if not backbone:
    for i in range(num_traverse):
        bfs_depth=sorted(list(nx.bfs_tree(g, source=sources[i], depth_limit=3).edges()))
        bfs_list.append(bfs_depth)
else: 
    for i in range(num_traverse):
        bfs_depth=sorted(list(nx.bfs_tree(g, source=min_vertex[i], depth_limit=3).edges()))
        bfs_list.append(bfs_depth)

merged = list(itertools.chain(*bfs_list))

if not backbone:
    for i in range(num_traverse):
        dfs_depth=sorted(list(nx.bfs_tree(g, source=sources[i], depth_limit=depth_limit_search).edges()))
        dfs_list.append(bfs_depth)
else: 
    for i in range(num_traverse):
        dfs_depth=sorted(list(nx.bfs_tree(g, source=min_vertex[i], depth_limit=depth_limit_search).edges()))
        dfs_list.append(bfs_depth)

merged_dfs = list(itertools.chain(*dfs_list))

reach=sps.lil_matrix((num_nodes, num_nodes), dtype=np.int8)
count=0
for (i,j) in merged:
    if count<query_budget:
        if i< num_nodes and j < num_nodes:
            reach[[i],[j]]=1
            count=count+1
    else:
        break

for (i,j) in list(g.edges):
        reach[i,j]=1
        
## Random walk with jump
       
object2=Graph_Sampling.SRW_RWF_ISRW()
sample2= object2.random_walk_sampling_with_fly_back(g,query_budget,jump_prob)
random_jump=sample2.edges()

## Forest Fore 
object4=Graph_Sampling.ForestFire()
sample4 = object4.forestfire(g,query_budget) 
FF=sample4.edges()

merged=FF
reach_FF=sps.lil_matrix((num_nodes, num_nodes), dtype=np.int8)
#merged=random_jump
            
#reach_jump=sps.lil_matrix((num_nodes, num_nodes), dtype=np.int8)
j=0
for i in merged:
    if j<query_budget:
        reach_FF[i[0],i[1]]=1
        j=j+1

#def getResult(X_train,X_test , rank):
#reach_minVertex        
model = NMF(n_components= rank, init='random', random_state=0)
W1 = model.fit_transform(reach)
H1 = model.components_
                       
HT=np.transpose(H1)

test_size=int(num_nodes*0.002)
reach_test=sps.lil_matrix((test_size, num_nodes), dtype=np.int8)
pred=sps.lil_matrix((test_size, num_nodes), dtype=np.int8)

nzeroo=np.argwhere(reach != 0)
count=0
while count<test_size/2:
      x=random.randint(0,test_size-1)
      y=random.randint(0,test_size-1)
      if g.has_node(x) and g.has_node(y): 
          if (x,y) not in nzeroo and has_path(g,x,y):
              reach_test[[x],[y]]=1 
              pred[[x],[y]]=W1[x].dot(HT[y])
              #print(W1[x].dot(HT[y]))
              count=count+1
              
count=0
while count<test_size/2:
      x=random.randint(0,test_size-1)
      y=random.randint(0,test_size-1)
      if  g.has_node(x) and g.has_node(y): 
          if [[x],[y]] not in nzeroo:
              reach_test[[x],[y]]=0
              pred[[x],[y]]=W1[x].dot(HT[y])
              count=count+1              
               
              

pred_arr=pred.toarray()
reach_test_dense=reach_test.toarray()
from sklearn.metrics import mean_squared_error
mean_squared_error(reach_test_dense, pred_arr)
scorer=metrics.explained_variance_score
scorer(reach_test_dense, pred_arr)

      
          
mse = sklearn.metrics.mean_squared_error(actual, predicted)

rmse = math.sqrt(mse)

def get_score(model, data, scorer=metrics.explained_variance_score):
    """ Estimate performance of the model on the data """
    prediction = model.inverse_transform(model.transform(data))
    return scorer(data, prediction)

print('test set performance')
nmf = decomposition.NMF(n_components=rank).fit(reach)

reach_test_dense=reach_test.toarray()
print(get_score(nmf, reach_test_dense))



prediction = nmf.inverse_transform(model.transform(reach_test_dense))

################# predict paths
pos={}
neg={}

path_pos=[]
path_neg=[]
path_neg_test=[] 
path_pos_test=[]

train_size=query_budget/5
test_size=500


def add_label(path_pos,path_neg):
             
    array = np.array(path_pos)
    test1=array.reshape((len(path_pos),rank))
    
    
    
    array2 = np.array(path_neg)
    test2=array2.reshape((len(path_neg),rank))
    
    
    label1=np.ones(len(path_pos))
    featuretest=np.insert(test1,rank,label1,axis=1)
          
    label2=np.zeros(len(path_neg))
    featuretest2=np.insert(test2,rank,label2,axis=1)
    
    
    all12=np.concatenate((featuretest,featuretest2))
    return all12

for k in merged:
        if len(path_pos)<train_size:
            print(HT[k[1]])
            path_pos.append(np.multiply(W1[k[0]],HT[k[1]]))
        
    
j=0
i=0
while i<train_size or j<test_size:
      x=random.randint(0,num_nodes-1)
      y=random.randint(0,num_nodes-1)
      if g.has_node(x) and g.has_node(y):
          if (x,y) not in merged and not has_path(g,x,y) and i<train_size:
             path_neg.append(np.multiply(W1[x],HT[y]))
             i=i+1
             print("train")
             print (i)
          if (x,y) not in merged and not has_path(g,x,y) and i==train_size and j<test_size:
             path_neg_test.append(np.multiply(W1[x],HT[y]))
             j=j+1
             print("test")
             print(j)
         
path_pos_test=[]
while len(path_pos_test)<test_size:
      x=random.randint(0,num_nodes-1)
      y=random.randint(0,num_nodes-1)
      if g.has_node(x) and g.has_node(y): 
          if (x,y) not in merged and has_path(g,x,y):
              print(W1[x])
              path_pos_test.append(np.multiply(W1[x],HT[y]))         
         
'''       
while len(path_neg_test)<test_size:
      x=random.randint(0,num_nodes-1)
      y=random.randint(0,num_nodes-1)
      if (x,y) not in merged and not has_path(x,y):
          path_neg.append(np.multiply(W1[x],HT[y]))
'''    

    
all12_train = add_label(path_pos,path_neg) 
y_train=all12_train[:,-1]
X_train=all12_train[:,0:rank-1]

all12_test = add_label(path_pos_test,path_neg_test) 
y_test=all12_test[:,-1]
X_test=all12_test[:,0:rank-1]

#X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2)

target_names = [ 'class 0', 'class 1']
unique_elements, counts_elements = np.unique(y_pred, return_counts=True)
print(unique_elements)
clf = RandomForestClassifier(n_estimators=15)
#clf = LogisticRegression(random_state=0, solver='lbfgs',multi_class='multinomial')


clf.fit(X_train,y_train)

y_pred=clf.predict(X_test)
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

print(classification_report(y_test, y_pred, target_names=target_names))
time_end = time.perf_counter()
time_elapsed = (time_end - time_start)

import resource
memMb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
confusion_matrix(y_test, y_pred, labels=[0, 1])      




## randoly select source and target
for i in range(query_budget):
     source=random.randint(0,num_nodes)
     dest=random.randint(0,num_nodes)
     if has_path(g,source,dest):
         reach[source,dest]=1

def min_weighted_vertex_cover(G, weight=None):
    r"""2-OPT Local Ratio for Minimum  Vertex Cover

    Find an approximate minimum vertex cover of a graph.

    Notes
    -----
    Local-Ratio algorithm for computing an approximate vertex cover.
    Algorithm greedily reduces the costs over edges and iteratively
    builds a cover. Worst-case runtime is `O(|E|)`.

    References
    ----------
    .. [1] Bar-Yehuda, R., & Even, S. (1985). A local-ratio theorem for
       approximating the weighted vertex cover problem.
       Annals of Discrete Mathematics, 25, 27–46
       http://www.cs.technion.ac.il/~reuven/PDF/vc_lr.pdf
    """
    weight_func = lambda nd: nd.get(weight, 1)
    cost = dict((n, weight_func(nd)) for n, nd in G.nodes(data=True))

    # while there are edges uncovered, continue
    for u,v in G.edges_iter():
        # select some uncovered edge
        min_cost = min([cost[u], cost[v]])
        cost[u] -= min_cost
        cost[v] -= min_cost

    return set(u for u in cost if cost[u] == 0)

visited_bfs = [] # List to keep track of visited nodes.
queue_bfs = []     #Initialize a queue

def bfs(visited_bfs, graph, node):
  visited_bfs.append(node)
  queue_bfs.append(node)

  while queue_bfs:
    s = queue_bfs.pop(0) 
    print (s, end = " ") 

    for neighbour in graph[s]:
      if neighbour not in visited:
        visited.append(neighbour)
        queue_bfs.append(neighbour)
        
def has_path(g,i,j):
    bfs_nodes=bfs(g,i)
    if j in bfs_nodes:
        return True


def dfs_tree(G, source=None, depth_limit=None):
  
    T = nx.DiGraph()
    if source is None:
        T.add_nodes_from(G)
    else:
        T.add_node(source)
    T.add_edges_from(dfs_edges(G, source, depth_limit))
    return T

def dfs_edges(G, source=None, depth_limit=None):
    
    if source is None:
        # edges for all components
        nodes = G
    else:
        # edges for components with source
        nodes = [source]
    visited = set()
    if depth_limit is None:
        depth_limit = len(G)
    for start in nodes:
        if start in visited:
            continue
        visited.add(start)
        stack = [(start, depth_limit, iter(G[start]))]
        while stack:
            parent, depth_now, children = stack[-1]
            try:
                child = next(children)
                if child not in visited:
                    yield parent, child
                    visited.add(child)
                    if depth_now > 1:
                        stack.append((child, depth_now - 1, iter(G[child])))
            except StopIteration:
                stack.pop()


def bfs_edges(G, source, reverse=False, depth_limit=None):
     
    if reverse and G.is_directed():
        successors = G.predecessors
    else:
        successors = G.neighbors
    # TODO In Python 3.3+, this should be `yield from ...`
    for e in generic_bfs_edges(G, source, successors, depth_limit):
        return e

def generic_bfs_edges(G, source, neighbors=None, depth_limit=None):
    visited = {source}
    if depth_limit is None:
        depth_limit = len(G)
    queue = deque([(source, depth_limit, neighbors(source))])
    while queue:
        parent, depth_now, children = queue[0]
        try:
            child = next(children)
            if child not in visited:
                yield parent, child
                visited.add(child)
                if depth_now > 1:
                    queue.append((child, depth_now - 1, neighbors(child)))
        except StopIteration:
            queue.popleft()def bfs_tree(G, source, reverse=False, depth_limit=None):
   
    T = nx.DiGraph()
    T.add_node(source)
    edges_gen = bfs_edges(G, source, reverse=reverse, depth_limit=depth_limit)
    T.add_edges_from(edges_gen)
    return T
######Matrix Completion

 
import implicit

# initialize a model
model = implicit.als.AlternatingLeastSquares(factors=50)
model.fit(reach)

user_items = reach.T.tocsr()
recommendations = model.recommend(20, user_items)
preds_reach=model.item_factors.dot(model.user_factors.T).tocsr()
