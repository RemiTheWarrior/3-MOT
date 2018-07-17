import xml.etree.ElementTree as ET


def find_number_of_volumes_in_each_step_file(input_locations):
    body_ids=''
    volumes_in_each_step_file=[]
    for i in range(0,len(input_locations)):
      current_vols =cubit.parse_cubit_list("volume", "all")
      print('input       ',    input_locations[i])
      if input_locations[i].endswith('.sat'):
        cubit.cmd('import acis "'+input_locations[i]+'" nofreesurfaces separate_bodies')
      if input_locations[i].endswith('.stp') or input_locations[i].endswith('.step'):
        cubit.cmd('import step "'+input_locations[i]+'" heal')
      #body_ids=body_ids+' '+str(i+1)
      all_vols =cubit.parse_cubit_list("volume", "all")
      new_vols = set(current_vols).symmetric_difference(set(all_vols))
      print('all_vols    ',str(all_vols))
      print('current_vols',str(current_vols))
      print('new_vols    ',str(new_vols))
      #volumes_in_each_step_file.append(new_vols)
      new_vols=map(str, new_vols)
      new_vols=' '.join(new_vols)
      volumes_in_each_step_file.append(new_vols.split())
    print('volumes_in_each_step_file')
    print(volumes_in_each_step_file)
    print('body_ids')
    print(body_ids)
    return volumes_in_each_step_file

def find_shared_surfaces_between_coolant_and_structure(volumes_in_coolant_step_file):
  print('looking for merged surfaces')
  surfaces_in_all_volumes = cubit.parse_cubit_list("surface"," in volume all ")
  surfaces_in_all_coolant_volumes = cubit.parse_cubit_list("surface"," in volume "+str(' '.join([item for sublist in volumes_in_coolant_step_file for item in sublist])))
  print('surfaces_in_all_coolant_volumes',surfaces_in_all_coolant_volumes)
  list_of_merged_surfaces =[]
  for surface in surfaces_in_all_volumes:
      is_merged = cubit.is_merged("surface", surface)
      #print(surface, is_merged)
      if is_merged == False:
          cubit.cmd('color surface '+str(surface)+ ' lightslateblue')
      if is_merged == True and surface in surfaces_in_all_coolant_volumes:
          cubit.cmd('color surface '+str(surface)+ ' orchid')
          # print('cooling surface id ',surface)
          list_of_merged_surfaces.append(surface)
          cubit.cmd('highlight surface '+str(surface))  
  return list_of_merged_surfaces

def find_external_surfaces(volumes):

    return 1

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def read_arguments_from_json_file(aprepro_vars):
  json_input = str(cubit.get_aprepro_value_as_string("json_input"))
  print('json_inputfile ='+str(json_input))
  with open(json_input) as f:
    data = json.load(f)
    pprint(data)
  data=byteify(data)
  quality= data["quality"]
  outputfile = data["outputfile"]
  coolant_step_files= data["void"] #todo rename coolant by void
  structure_step_files= data["structure"]
  return quality, outputfile, coolant_step_files, structure_step_files

def read_arguments_from_terminal_input(aprepro_vars):
  if "quality" in aprepro_vars:
    quality = str(cubit.get_aprepro_value_as_string("quality"))
    print('quality ='+str(quality))  
  else:
    quality = '10'
  if "outputfile" in aprepro_vars:
    outputfile = str(cubit.get_aprepro_value_as_string("outputfile"))
    print('outputfile ='+str(outputfile))  
  else:
    outputfile = 'mesh_and_markers.xdmf'
  if "coolant" in aprepro_vars:
    coolant_step_files = cubit.get_aprepro_value_as_string("coolant").split(',')
    print('coolant geometry file ='+str(coolant_step_files))
  if "structure" in aprepro_vars:
    structure_step_files = cubit.get_aprepro_value_as_string("structure").split(',')
    print('structure geometry files ='+str(structure_step_files))
    print('number of structure geometry files ='+str(len(structure_step_files)))
  return quality, outputfile, coolant_step_files, structure_step_files

def mesh_and_remesh_till_done(quality):
  cubit.cmd('volume all scheme Tetmesh')
  cubit.cmd('volume all scheme tetmesh proximity layers off geometry approximation angle 15 geometric sizing on ')
  cubit.cmd('volume all size auto factor '+str(quality)) # replace with sizing function 10 times smaller than smallest size in model
  cubit.cmd('volume all tetmesh growth_factor 1 ')
  cubit.cmd('Trimesher surface gradation 1.3')
  cubit.cmd('Trimesher volume gradation 1.3')
  cubit.cmd('mesh volume all')
  for step_file in volumes_in_structure_step_files:
    for volume in step_file:
      #print(volume)
      #print(cubit.is_meshed("volume", int(volume))) 
      if cubit.is_meshed("volume", int(volume)) == False:
        print(volume)
        print(cubit.is_meshed("volume", int(volume)))         
        print('full geometry ot meshed, try changing the quality')
        sys.exit()



#Meshing

aprepro_vars = cubit.get_aprepro_vars()

print("Found the following aprepro variables:")
print(aprepro_vars)

for var_name in aprepro_vars:
  val = cubit.get_aprepro_value_as_string(var_name)
  print("{0} = {1}".format(var_name, val))


cubit.cmd('reset')

volumes_in_structure_step_files = find_number_of_volumes_in_each_step_file(structure_step_files)
print('volumes_in_each_step_file',volumes_in_structure_step_files)

f1 = open('structure_step_file_and_volumes.txt', 'w') 
for structure_step_file,volumes_in_structure_step_file in zip(structure_step_files , volumes_in_structure_step_files):
  f1.write(structure_step_file +' ' + ' '.join(str(i) for i in volumes_in_structure_step_file) +'\n')
f1.close()

volumes_in_coolant_step_file = find_number_of_volumes_in_each_step_file(coolant_step_files)
print('volumes_in_each_step_file',volumes_in_coolant_step_file)

cubit.cmd('imprint body all')
cubit.cmd('merge tolerance 1.e-6')
cubit.cmd('merge all')


mesh_and_remesh_till_done(quality)

nodes_in_volumes = sorted(cubit.parse_cubit_list("node"," in volume all "))
nodal_coordinates_list = []
# print('nodes_in_volumes',nodes_in_volumes)
for node_id in nodes_in_volumes:
    nodal_coordinates_list.append(cubit.get_nodal_coordinates(node_id))
print(nodal_coordinates_list)

tets_in_volumes = cubit.parse_cubit_list("tet"," in volume all ")
nodes_in_tests_list=[]
for tet_id in tets_in_volumes:
    nodes_in_tets = cubit.parse_cubit_list("node"," in tet "+str(tet_id))
    nodes_in_tests_list.append(nodes_in_tets)




#Writing mesh file
def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i


# create the file structure

data = ET.Element('Domain')
Grid = ET.SubElement(data, 'Grid')
Grid.set('Name','mesh')
Grid.set('GridType','Uniform')


#Writing the nodes of all the cells in the mesh
Topology = ET.SubElement(Grid,'Topology')
Topology.set('NumberOfElements',str(len(tets_in_volumes)))
Topology.set('TopologyType','Tetrahedron')
Topology.set('NodesPerElement','4')


DataItem = ET.SubElement(Topology,'DataItem')
DataItem.set('Dimensions',str(len(tets_in_volumes))+' 4')
DataItem.set('NumberType','UInt')
DataItem.set('Format','XML')
string_of_text=''
for tet_id in tets_in_volumes:
    nodes_in_tets=cubit.parse_cubit_list("node"," in tet "+str(tet_id))
    string_of_text += str(nodes_in_tets(0)-1)+' '+str(nodes_in_tets(1)-1)+' '+str(nodes_in_tets(2)-1)+' '+str(nodes_in_tets(3)-1)+'\n'
cells.text=string_of_text


#Writing the coordinates of all the nodes in the mesh
Geometry = ET.SubElement(Grid, 'Geometry')
Geometry.set('GeometryType','XYZ')
DataItem = ET.SubElement(Geometry,'DataItem')
DataItem.set('Dimensions',str(len(nodal_coordinates_list))+' 3')
DataItem.set('Format','XML')
string_of_text=''
for coords in nodal_coordinates_list:
    string_of_text += str(coords(0))+' '+str(coords(1))+' '+str(coords(2))+'\n'
DataItem.text=string_of_text


#Writing the corresponding volume of all the cells in the mesh
Attribute=ET.SubElement(Grid,'Attribute')
Attribute.set('Name','VolumeMarker')
all_volumes = cubit.parse_cubit_list("volume", ' all')
all_surfaces = cubit.parse_cubit_list("surface", ' all')
string_of_text=''
tets_in_each_volume = []
for volume in all_volumes:
  tets_in_each_volume.append(cubit.get_volume_tets(volume))
for tet_id  in tets_in_volumes:
    for tets_in_the_volume , volume in zip(tets_in_each_volume,all_volumes):
        if tet_id in tets_in_the_volume:
            string_of_text += '\n'+str(volume)
            break
Attribute.text=string_of_text


##Writing all the nodes of all the triangles in the mesh
Grid = ET.SubElement(data, 'Grid')
Grid.set('Name','mesh')
Grid.set('GridType','Uniform')


triangles_in_tets = sorted(cubit.parse_cubit_list("tri"," in tet all "))
Topology = ET.SubElement(Grid,'Topology')
Topology.set('NumberOfElements',str(len(triangles_in_tets)))
Topology.set('TopologyType','Triangle')
Topology.set('NodesPerElement','3')
DataItem = ET.SubElement(Topology,'DataItem')
DataItem.set('Dimensions',str(len(triangles_in_tets))+' 3')
DataItem.set('NumberType','UInt')
DataItem.set('Format','XML')

string_of_text=''
for tri_ids in triangles_in_tets:
    nodes_in_triangles = cubit.parse_cubit_list("node"," in tri "+str(tri_ids))
    # print(nodes_in_triangles)
    for i in nodes_in_triangles:
      string_of_text+=str(i-1)+' '
    string_of_text+='\n' 
DataItem.text=string_of_text



##Writing the surfaces of all triangles in the mesh (0 if not on an external surface)
Geometry=ET.SubElement(Grid,'Geometry')
Attribute=ET.SubElement(Grid,'Attribute')
Attribute.set('Name','surface_marker')
Attribute.set('AttributeType','scalar')
Attribute.set('Center','Cell')
DataItem = ET.SubElement(Attribute,'DataItem')
DataItem.set('Dimensions',str(len(triangles_in_tets))+' 1')

string_of_text=''
tri_in_external_surface = []
all_external_surfaces=find_external_surfaces()
for surface in all_external_surfaces:
  tri_in_external_surface.append(cubit.parse_cubit_list("tri"," in surface "+' '+str(surface)))
string_of_text=''
for tri_id  in triangles_in_tets:
  Found=False
  for i in range(len(tri_in_external_surface)):
    if tri_id in tri_in_external_surface(i):
      Found=True
  if Found==True:
    string_of_text+=str(all_external_surfaces(i))+'\n'
  else:
    string_of_text+='0 \n'
DataItem.text=string_of_text
      


  

indent(data)
# create a new XML file with the results
mydata = ET.tostring(data)  
myfile = open("meshtest.xdmf", "w")  
myfile.write(mydata)