import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xml.etree.ElementTree as gfg
import argparse
import numpy
import xml.dom.minidom
from lxml import etree, objectify
import re



class Topic:
    """
    This class shows a topic for task 1. Each topic has an topic_id which is str, a title and question which
    is the question body and a list of tags.
    """

    def __init__(self, topic_id, title, question, tags):
        self.topic_id = topic_id
        self.title = title
        self.question = question
        self.lst_tags = tags


class TopicReader:
    """
    This class takes in the topic file path and read all the topics into a map. The key in this map is the topic id
    and the values are Topic which has 4 attributes: id, title, question and list of tags for each topic.

    To see each topic, use the get_topic method, which takes the topic id and return the topic in Topic object and
    you have access to the 4 attributes mentioned above.
    """

    def __init__(self, topic_file_path):
        self.map_topics = self.__read_topics(topic_file_path)

    def __read_topics(self, topic_file_path):
        map_topics = {}
        tree = ET.parse(topic_file_path)
        root = tree.getroot()
        for child in root:
            topic_id = child.attrib['number']
            title = child[0].text
            question = child[1].text
            lst_tag = child[2].text.split(",")
            map_topics[topic_id] = Topic(topic_id, title, question, lst_tag)
        return map_topics

    def get_topic(self, topic_id):
        if topic_id in self.map_topics:
            return self.map_topics[topic_id]
        return None


def read_topics(file_path):
    map_formulas = {}
    with open(file_path) as csv_file:
        csvreader = csv.reader(csv_file, delimiter='\t')
        next(csvreader)
        for row in csvreader:
            formula_id = row[0]
            topic_id = row[1]
            if topic_id in map_formulas:
                map_formulas[topic_id].append(formula_id)
            else:
                map_formulas[topic_id] = [formula_id]
    return map_formulas


def separated_duplicate_related(file_path, related_path, duplicate_path):
    related_csv = open(related_path, "w", newline='')
    duplicated_csv = open(duplicate_path, "w", newline='')

    duplicate_csv_writer = csv.writer(duplicated_csv, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    related_csv_writer = csv.writer(related_csv, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    with open(file_path, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t', quotechar='"')
        for row in spamreader:
            related = int(row[3])
            if related == 2:
                duplicate_csv_writer.writerow([row[0], row[1], row[2], "1"])
            else:
                related_csv_writer.writerow([row[0], row[1], row[2], "1"])
    related_csv.close()
    duplicated_csv.close()


def read_tsv_file(tsv_file):
    result = {}
    with open(tsv_file, encoding="utf-8") as csv_file:
        csvreader = csv.reader(csv_file, delimiter='\t')
        next(csvreader)
        for row in csvreader:
            formula_id = row[0]
            formula = row[4]
            result[formula_id] = formula
    return result


def write_xml(topic_reader, slt_items, save_path_file):
    root = gfg.Element("topics")
    # xml = root.createElement('topics')
    for topic_id in topic_reader.map_topics:
        m1 = gfg.Element("topic")
        b1 = gfg.SubElement(m1, "num")
        b1.text = topic_id
        b2 = gfg.SubElement(m1, "query")
        b3 = gfg.SubElement(b2, "formula")
        q_id = topic_reader.map_topics[topic_id].title
        b3.attrib['id'] = q_id
        mathml = slt_items[q_id]
        print(xml.etree.ElementTree.fromstring(re.sub(' xmlns="[^"]+"', '', mathml, count=1)))
        b3.append(xml.etree.ElementTree.fromstring(mathml))
        #b3.text = xml.etree.ElementTree.tostring(xml.etree.ElementTree.fromstring(mathml))

        root.append(m1)
    # root.appendChild(xml)

    tree = gfg.ElementTree(root)
    xml.dom.minidom.parseString(xml.etree.ElementTree.tostring(root))
    with open(save_path_file, "w") as file:
        dom = xml.dom.minidom.parseString(xml.etree.ElementTree.tostring(root))

        file.write(dom.toprettyxml()
                   .replace('xmlns:ns0="http://www.w3.org/1998/Math/MathML"', "")
                   .replace('ns0:', '')
                   .replace('encoding="MathML-Content"', '')
                   )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--topics', type=str)
    parser.add_argument('-ts', '--tsv', type=str)
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    topic_reader = TopicReader(args.topics)  # "Topics_Task2_2021_V1.1.xml"
    slt_items = read_tsv_file(args.tsv)  # "Topics_2021_Formulas_OPT_V1.1.tsv"
    write_xml(topic_reader, slt_items, args.output)  # "opt_topic2.xml"
    with open(args.output) as xmldata:
        # xml = xml.dom.minidom.parseString(xmldata.read())  # or xml.dom.minidom.parseString(xml_string)
        # xml_pretty_str = xml.toprettyxml()
        print(xmldata.read())