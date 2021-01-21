import csv
import os
import time
import sys
from xml.dom import minidom
from sys import argv

import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from src.python.utility.dir2doclist import create_doclist


def read_file_save_formula(directory, base_dir):
    "Takes in the csv file and save each formula in a separate file"
    count = 0
    counter = 0
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    for file_path in os.listdir(directory):
        with open(directory+"/"+file_path, newline='', encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
            next(csv_reader)
            for row in csv_reader:
                # try:
                formula_id = row[0]
                xml_data = row[5]
                # 100,000 formula per folder
                if count % 100000 == 0:
                    counter += 1
                    print(os.path.join(base_dir, str(counter)))
                    if not os.path.exists(os.path.join(base_dir,str(counter))):
                        os.mkdir(os.path.join(base_dir, str(counter)))
                    count = 0
                    time.sleep(4)
                count += 1
                file_path = os.path.join(base_dir, str(counter), str(formula_id)+".mml")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(str(xml_data))
                # except:
                #     print("error")



def create_query_file_tangents(topic_file_path, math_ml_file_path, result_file_path):
    formula_map = {}
    data = ET.Element('topics')
    with open(math_ml_file_path, newline='', encoding="utf-8") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        next(csv_reader)
        for row in csv_reader:
            # try:
            formula_id = row[0]
            xml_data = row[4]
            xml_data = xml_data
            formula_map[formula_id] = xml_data
            # break
    tree = ET.parse(topic_file_path)
    root = tree.getroot()
    for child in root:
        topic_number = child.attrib['number']
        formula_id = child[0].text

        topic_xml = ET.SubElement(data, 'topic')
        num_xml = ET.SubElement(topic_xml, 'num')
        num_xml.text = topic_number
        query_xml = ET.SubElement(topic_xml, 'query')
        formula_xml = ET.SubElement(query_xml, 'formula')
        formula_xml.set('id', str(formula_id))
        formula_xml.text = formula_map[formula_id]
    rough_string = ElementTree.tostring(data, 'utf-8')
    reparsed = minidom.parseString(rough_string)

    myfile = open(result_file_path, "w", encoding="utf-8")
    myfile.write(reparsed.toprettyxml(indent="  "))


if __name__ == "__main__":

    csv.field_size_limit(sys.maxsize)
    # parent_repo = argv[1]

    # doclist_file = argv[3]

    read_file_save_formula("../../../../opt_representation_v2", "../../../../raw-data-opt")
    # create_query_file_tangents("Topics_V1.1.xml", "Formula_topics_opt_V2.0.tsv", "opt_queries3.xml")

    #########################
    # ARQMath
    #########################
    create_doclist("../../../cntl/opt-big.txt", ["../../../../raw-data-opt/"])
