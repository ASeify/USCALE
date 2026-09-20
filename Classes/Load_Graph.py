import networkx as nx
import os
import sys
import scipy
from termcolor import colored


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if not (CURRENT_DIR in sys.path):
    sys.path.append(CURRENT_DIR)

from Bcolors_Class import Bcolors
from Files_Handler_Class import Files_Handler

files_handler_obj = Files_Handler()
bcolors = Bcolors()

class Load_Graph:

    color_list = ["light_red", "light_green", "light_yellow",
                    "light_blue","light_magenta", "light_cyan",
                    "blue", "red", "white", "green", "yellow",
                        "magenta", "cyan", ]

    @staticmethod
    def load_monoplex_graph(file_path:str, file_info:dict, 
                            convert_node_labels:bool=False,nodes_first_label:int=None,
                            convert_undirected:bool=True, tabs='\t')->nx.Graph:
    
        if not (os.path.exists(file_path)):
            print(f"Error: File {file_path} not found.")
            sys.exit(1)
        else:
            # print(file_info)
            if (file_info['type'] == ".edgelist" or file_info['type'] == ".edges" 
                or file_info['type'] == ".txt"):
                graph = nx.read_edgelist(file_path, comments="#")
            elif (file_info['type'] == ".gml"):
                graph = nx.read_gml(file_path)
            elif (file_info['type'] == ".mtx"):
                graph = nx.read_edgelist(file_path, comments="#")
            elif (file_info['type'] == ".csv"):
                graph = nx.read_edgelist(file_path, delimiter=' ', nodetype=str)
                if graph.number_of_nodes() == 0:
                    graph = nx.read_edgelist(file_path, delimiter='\t', nodetype=str)
                if graph.number_of_nodes() == 0:
                    graph = nx.read_edgelist(file_path, delimiter=',', nodetype=str)
                if 'source' in graph:
                    graph.remove_node('source')
                if 'target' in graph:
                    graph.remove_node('target')
            
            if graph.number_of_nodes() > 0:
                print(f"{tabs}{bcolors.green_fg}Graph with {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{graph.number_of_nodes()}{bcolors.end_color}" +
                    f"{bcolors.green_fg} nodes and {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{graph.number_of_edges()}{bcolors.end_color}" +
                    f"{bcolors.green_fg} edges loaded successfully.{bcolors.end_color}")
                if convert_node_labels:
                    graph = nx.convert_node_labels_to_integers(graph, first_label=nodes_first_label, ordering='default', label_attribute='orginal_label')#, label_attribute='old_label')
                    print(f"{tabs}Convert node labels to integers. Nodes first label is {bcolors.yellow_fg}{bcolors.bold}{nodes_first_label}{bcolors.end_color}" +
                        f" and Nodes last label is {bcolors.yellow_fg}{bcolors.bold}{nodes_first_label + graph.number_of_nodes()-1}{bcolors.end_color}")
                if convert_undirected:
                    if nx.is_directed(graph):
                        graph = graph.to_undirected()
            else:
                print(f"{tabs}{bcolors.red_fg}No nodes found in the graph.{bcolors.end_color}")
                graph = nx.Graph()
        return graph
    
    @staticmethod
    def load_multilayer_graph(file_path:str, network_type:str="Alaska Master", directed:bool=False,
                              delimiter:str=None, tabs:str='', print_layer_info:bool=True)->list[nx.Graph]:
        entra_layer_edges = {}
        intra_layer_edges = {}
        labels = {}
        # layer_id = 1
        if network_type != "Matlab File":

            try:
                with open(file_path, 'r') as file:
                    for line in file:
                        line = line.strip()
                        if line != None and line != "" and line != "\n" and line[0] != "#" and line[0] != "%":
                            if delimiter is None:
                                if "," in line:
                                    content_parts = line.split(",")
                                elif "\t" in line:
                                    content_parts = line.split("\t")
                                else:
                                    content_parts = line.split(" ")
                            else:
                                content_parts = line.split(delimiter)

                            if network_type == "Multiplex Edges" or network_type == "LFR":
                                if len(content_parts) >= 3:
                                    source_node_id = content_parts[0].strip()
                                    destination_node_id = content_parts[1].strip()
                                    layer_id = content_parts[2].strip()
                                    if not(layer_id in entra_layer_edges.keys()):
                                        entra_layer_edges[layer_id] = []
                                    entra_layer_edges[layer_id].append((source_node_id, destination_node_id))

                            if network_type == "Alaska Master":
                                if len(content_parts) >= 4:
                                    source_node_id = content_parts[0].strip()
                                    source_layer_id = content_parts[1].strip()
                                    destination_node_id = content_parts[2].strip()
                                    destination_layer_id = content_parts[3].strip()
                                    if source_layer_id == destination_layer_id:
                                        layer_id = source_layer_id
                                        if not(layer_id in entra_layer_edges.keys()):
                                            entra_layer_edges[layer_id] = []
                                        entra_layer_edges[layer_id].append((source_node_id, destination_node_id))
                                    else:
                                        if not(source_layer_id in intra_layer_edges.keys()):
                                            intra_layer_edges[source_layer_id] = {}
                                        if not(destination_layer_id in intra_layer_edges[source_layer_id].keys()):
                                            intra_layer_edges[source_layer_id][destination_layer_id] = []
                                        intra_layer_edges[source_layer_id][destination_layer_id].append((source_node_id, destination_node_id))

                                        if not(destination_layer_id in intra_layer_edges.keys()):
                                            intra_layer_edges[destination_layer_id] = {}
                                        if not(source_layer_id in intra_layer_edges[destination_layer_id].keys()):
                                            intra_layer_edges[destination_layer_id][source_layer_id] = []
                                        intra_layer_edges[destination_layer_id][source_layer_id].append((destination_node_id, source_node_id))
                file.close()
            except Exception as e:
                print(e)
            
            graphs_of_network = []
            i, j = 0, 0
            for k, v in entra_layer_edges.items():
                if len(v) > 0:
                    graphs_of_network.append(nx.Graph())
                    graphs_of_network[-1].add_edges_from(v)
                    graphs_of_network[-1].graph["id"]  = k
                    if print_layer_info:
                        print(colored(f"{tabs}Layer {i+1}: {graphs_of_network[-1].number_of_nodes()} Node And " +
                                    f"{graphs_of_network[-1].number_of_edges()} Edge", Load_Graph.color_list[j]))
                    i += 1
                    j += 1
                    if j >= len(Load_Graph.color_list):
                        j = 0
            network_entier_nodes_list = []
            for graph in graphs_of_network:
                if graph.number_of_nodes() > 0:
                    network_entier_nodes_list.extend(list(graph.nodes()))
                else:
                    graphs_of_network.remove(graph)
            network_entier_nodes_list = list(set(network_entier_nodes_list))
            network_entier_nodes_count = len(network_entier_nodes_list)
            print(f"{tabs}{bcolors.green_fg}Network with {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{network_entier_nodes_count}{bcolors.end_color}" +
                f"{bcolors.green_fg} nodes and {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{len(entra_layer_edges)}{bcolors.end_color}" +
                f"{bcolors.green_fg} layers loaded successfully.{bcolors.end_color}")
            
            return graphs_of_network, network_entier_nodes_list, labels
        
        else:
            file_info = files_handler_obj.get_file_path_info(file_path)
            graphs_of_network = []
            file_path = os.path.join(file_info['path'], file_info['name'] + file_info['type'])
            data = scipy.io.loadmat(file_path)
            data_keys = list(data.keys())
            layers_data = data[data_keys[3]]
            for item in layers_data:
                if directed:
                    graphs_of_network.append(nx.from_scipy_sparse_array(item[0], create_using=nx.DiGraph))
                else:
                    graphs_of_network.append(nx.from_scipy_sparse_array(item[0], create_using=nx.Graph))
            labels = None
            if len(data_keys) > 4:
                try:
                    if file_info['name'] in ["UCI_mfeat","cora","citeseer"]:
                        labels = data[data_keys[4]].toarray().transpose()[0]
                    else:
                        labels = data[data_keys[4]].toarray()[0]
                    nodes_comms = {}
                    for i, item in enumerate(labels):
                        nodes_comms[str(i)] = int(item)            
                    labels = nodes_comms
                except:
                    labels = data[data_keys[4]]
                    nodes_comms = {}
                    node_counter = 0
                    for graph in graphs_of_network:
                        for node in graph.nodes():
                            if node not in nodes_comms.keys():
                                nodes_comms[node] = {}
                            if labels[node_counter][0] not in nodes_comms[node].keys():
                                nodes_comms[node][labels[node_counter][0]] = 1
                            else:
                                nodes_comms[node][labels[node_counter][0]] += 1
                            node_counter += 1
                    labels = {}
                    for node, comms in nodes_comms.items():
                        node = str(node)
                        if len(comms) == 1:
                            labels[node] = list(comms.keys())[0]
                        elif len(comms) > 1:
                            labels[node] = max(comms, key=comms.get)
             
            
            i, j = 0, 0
            network_entier_nodes = []
            entra_layer_edges = []
            for graph in graphs_of_network:
                network_entier_nodes.extend(list(graph.nodes()))
                entra_layer_edges.extend(list(graph.edges()))
                if print_layer_info:
                    print(colored(f"{tabs}Layer {i+1}: {graph.number_of_nodes()} Node And " +
                                f"{graph.number_of_edges()} Edge", Load_Graph.color_list[j]))
                i += 1
                j += 1
            network_entier_nodes = list(set(network_entier_nodes))
            network_entier_nodes_count = len(network_entier_nodes)
            print(f"{tabs}{bcolors.green_fg}Network with {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{network_entier_nodes_count}{bcolors.end_color}" +
                f"{bcolors.green_fg} nodes and {bcolors.end_color}{bcolors.yellow_fg}{bcolors.bold}{len(entra_layer_edges)}{bcolors.end_color}" +
                f"{bcolors.green_fg} layers loaded successfully.{bcolors.end_color}")
            return graphs_of_network, network_entier_nodes, labels
    