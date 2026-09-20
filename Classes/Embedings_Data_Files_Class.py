from tqdm import tqdm
import os
import sys
import lzma
import json
import networkx as nx


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if not (CURRENT_DIR in sys.path):
    sys.path.append(CURRENT_DIR)

from Files_Handler_Class import Files_Handler
from Bcolors_Class import Bcolors
from Load_Graph import Load_Graph
from Get_Past_Results_Class import Get_Past_Results
from Generate_Embedings import Generate_Embedings

files_handler_obj = Files_Handler()
bcolors = Bcolors()
load_graph_obj = Load_Graph()
embeddings_obj = Generate_Embedings()


class Embedings_Data_Files:
    @staticmethod
    def load_data(load_method:str, file_path:str=None,
              embedding_attribute:str='Degree', embedding_method:str="Scale", embedding_type:str='Vector',
              walk_length:int=256, walk_depth:int=3, num_walks:int=1, umap_n_components:int=128, tabs:str=''):
        
        '''
        load_method = {A:Aggregated, SU:Separate UMAP, S:Separate}
        '''

        data = {'x':[], 'y':[]}
        load_status = False
        root_path = None
        if load_method == "A":
            if file_path is None:
                file_path = files_handler_obj.select_files('.xz', '.xz')
            file_path_info = files_handler_obj.get_file_path_info(file_path)
            root_path = file_path_info['path']
            print(f"{tabs}{bcolors.cyan_fg}{bcolors.underline}Root path: {root_path}{bcolors.ENDC}")
            print(f"{tabs}{bcolors.bold}{bcolors.italic}File name: {file_path_info['name'] + file_path_info['type']}{bcolors.ENDC}")
            try:
                with lzma.open(file_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
                    load_status = True
            except FileNotFoundError:
                print(f"{tabs}{bcolors.FAIL}File not found: {file_path}{bcolors.ENDC}")
        elif load_method == "SU":
            root_path = files_handler_obj.select_dir()
            if root_path is None or root_path == '':
                sys.exit(1)
            root_path += "/"
            print(f"{tabs}{bcolors.cyan_fg}{bcolors.underline}Root path: {root_path}{bcolors.ENDC}")
            files_list = files_handler_obj.get_files_by_extensions(root_path, '.xz')
            file_neme_pattern = f" nodes {embedding_attribute} {embedding_method} {embedding_type}"
            file_neme_pattern += f" wl={walk_length}, wd={walk_depth} nw={num_walks}"
            file_neme_pattern += f" umap={umap_n_components}.xz"
            selected_files = []
            for item in files_list:
                if item.endswith(file_neme_pattern):
                    selected_files.append(item)
            if len(selected_files) > 0:
                for item in tqdm(selected_files, desc="Loading files", unit="file"):
                    try:
                        with lzma.open(item, "rt", encoding="utf-8") as f:
                            temp_data = json.load(f)
                        
                        data['x'].extend(temp_data['embedings'])
                        data['y'].extend(temp_data['sirs'])
                        load_status = True

                    except FileNotFoundError:
                        load_status = False
                        print(f"{tabs}{bcolors.FAIL}File reading failed: {item}{bcolors.ENDC}")
            else:
                print(f"{tabs}{bcolors.bold}{bcolors.red_fg}Expected files not found.{bcolors.end_color}")
        elif load_method == "SB":
            root_path = files_handler_obj.select_dir()
            if root_path is None or root_path == '':
                sys.exit(1)
            root_path += "/"
            print(f"{tabs}{bcolors.cyan_fg}{bcolors.underline}Root path: {root_path}{bcolors.ENDC}")
            files_list = files_handler_obj.get_files_by_extensions(root_path, '.xz')
            file_neme_pattern = f" nodes {embedding_attribute} {embedding_method} {embedding_type}"
            file_neme_pattern += f" wl={walk_length}, wd={walk_depth} nw={num_walks}"
            file_neme_pattern += f" Balanced.xz"
            print(f"{tabs}Files Pattern: {file_neme_pattern}")
            selected_files = []
            for item in files_list:
                if item.endswith(file_neme_pattern):
                    selected_files.append(item)
            if len(selected_files) > 0:
                for item in tqdm(selected_files, desc="Loading files", unit="file"):
                    try:
                        with lzma.open(item, "rt", encoding="utf-8") as f:
                            temp_data = json.load(f)
                        
                        data['x'].extend(temp_data['embedings'])
                        data['y'].extend(temp_data['sirs'])
                        load_status = True

                    except FileNotFoundError:
                        load_status = False
                        print(f"{tabs}{bcolors.FAIL}File reading failed: {item}{bcolors.ENDC}")
            else:
                print(f"{tabs}{bcolors.bold}{bcolors.red_fg}Expected files not found.{bcolors.end_color}")
        elif load_method == "S":
            root_path = files_handler_obj.select_dir()
            if root_path is None or root_path == '':
                sys.exit(1)
            root_path += "/"
            print(f"{tabs}{bcolors.cyan_fg}{bcolors.underline}Root path: {root_path}{bcolors.ENDC}")
            networks_extensions = [".edges", ".edgelist", ".mtx", ".gml", ".txt"]
            networks_list = files_handler_obj.get_files_by_extensions(root_path, networks_extensions)
            beta, landa, epoch = 0.01, 0.7, 1000
            data = {}
            data['x'] = []
            data['y'] = []
            
            if len(networks_list) > 0:
                load_status = True
            i = 1
            for item in networks_list:
                infos = files_handler_obj.get_file_info(item)
                print(f"{bcolors.bold}{i} - {infos['name']}:{bcolors.end_color}")
                i += 1

                print(f"\t{bcolors.yellow_fg}Loading graph...{bcolors.end_color}")
                graph = load_graph_obj.load_monoplex_graph(item, infos)
                nx.set_node_attributes(graph, None, name='embedding')
                
                result_path = infos['path'] + infos['name'] + "/"
                embeddings = embeddings_obj.load_nodes_embedding(result_path, infos['name'],
                                                                embedding_method, embedding_type, embedding_attribute,
                                                                512, walk_depth, num_walks, 'lzma')
                
                for node in graph.nodes():
                    if str(node) in embeddings:
                        graph.nodes[node]['embedding'] = embeddings[str(node)][:walk_length]
                    elif int(node) in embeddings:
                        graph.nodes[node]['embedding'] = embeddings[int(node)][:walk_length]

                print(f"\t{bcolors.yellow_fg}Nodes SIR loading...{bcolors.end_color}")
                get_past_results_obj = Get_Past_Results(infos['path'], infos['name'])
                sir_status, nodes_sir = get_past_results_obj.get_past_SIR_results(beta, landa, epoch)
                if sir_status:
                    print(f"\t{bcolors.green_fg}Load SIR values done.{bcolors.end_color}")
                else:
                    print(f"\t{bcolors.bold}{bcolors.red_fg}Load SIR values failed.{bcolors.end_color}")

                for layer, node, sir_value in nodes_sir:
                    if str(node) in graph.nodes():
                        if graph.nodes[str(node)]['embedding'] != None:
                            data['x'].append(graph.nodes[str(node)]['embedding'])
                            data['y'].append(sir_value)
                    elif int(node) in graph.nodes():
                        if graph.nodes[int(node)]['embedding'] != None:
                            data['x'].append(graph.nodes[int(node)]['embedding'])
                            data['y'].append(sir_value)
        
        return load_status, data, root_path

    @staticmethod
    def write_data(file_name:str, data:dict):
        with lzma.open(file_name, "wt", encoding="utf-8") as f:
            json.dump(data, f)