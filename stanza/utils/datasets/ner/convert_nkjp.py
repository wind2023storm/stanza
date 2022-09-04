import argparse
import json
import os
import random
from tqdm import tqdm
from lxml import etree


NAMESPACES = {"x":"http://www.tei-c.org/ns/1.0"}
MORPH_FILE = "ann_morphosyntax.xml"
NER_FILE = "ann_named.xml"
SEGMENTATION_FILE = "ann_segmentation.xml"

def parse_xml(path):
    if not os.path.exists(path):
        return None
    et = etree.parse(path)
    rt = et.getroot()
    return rt


def get_node_id(node):
    # get the id from the xml node
    return node.get('{http://www.w3.org/XML/1998/namespace}id')


def extract_entities_from_subfolder(subfolder, nkjp_dir):
    # read the ner annotation from a subfolder, assign it to paragraphs
    ner_path = os.path.join(nkjp_dir, subfolder, NER_FILE)
    rt = parse_xml(ner_path)
    if rt is None:
        return None
    subfolder_entities = {}
    ner_pars = rt.xpath("x:TEI/x:text/x:body/x:p", namespaces=NAMESPACES)
    for par in ner_pars:
        par_entities = {}
        _, par_id = get_node_id(par).split("_")
        ner_sents = par.xpath("x:s", namespaces=NAMESPACES)
        for ner_sent in ner_sents:
            corresp = ner_sent.get("corresp")
            _, ner_sent_id  = corresp.split("#morph_")
            par_entities[ner_sent_id] = extract_entities_from_sentence(ner_sent)
        subfolder_entities[par_id] = par_entities
    par_id_to_segs = assign_entities(subfolder, subfolder_entities, nkjp_dir)
    return par_id_to_segs


def extract_entities_from_sentence(ner_sent):
    # extracts all the entity dicts from the sentence
    # we assume that an entity cannot span across sentences
    segs = ner_sent.xpath("x:seg", namespaces=NAMESPACES)
    sent_entities = {}
    for i, seg in enumerate(segs):
        ent_id = get_node_id(seg)
        targets = [ptr.get("target") for ptr in seg.xpath("x:ptr", namespaces=NAMESPACES)]
        orth = seg.xpath("x:fs/x:f[@name='orth']/x:string", namespaces=NAMESPACES)[0].text
        ner_type = seg.xpath("x:fs/x:f[@name='type']/x:symbol", namespaces=NAMESPACES)[0].get("value")
        ner_subtype_node = seg.xpath("x:fs/x:f[@name='subtype']/x:symbol", namespaces=NAMESPACES)
        if ner_subtype_node:
            ner_subtype = ner_subtype_node[0].get("value")
        else:
            ner_subtype = None
        entity = {"ent_id": ent_id,
                  "index": i,
                  "orth": orth,
                  "ner_type": ner_type,
                  "ner_subtype": ner_subtype,
                  "targets": targets}
        sent_entities[ent_id] = entity
    cleared_entities = clear_entities(sent_entities)
    return cleared_entities


def clear_entities(entities):
    # eliminates entities which extend beyond our scope
    resolve_entities(entities)
    entities_list = sorted(list(entities.values()), key=lambda ent: ent["index"])
    entities = eliminate_overlapping_entities(entities_list)
    for entity in entities:
        targets = entity["targets"]
        entity["targets"] = [t.split("morph_")[1] for t in targets]
    return entities


def resolve_entities(entities):
    # assign morphological level targets to entities
    resolved_targets = {entity_id: resolve_entity(entity, entities) for entity_id, entity in entities.items()}
    for entity_id in entities:
        entities[entity_id]["targets"] = resolved_targets[entity_id]


def resolve_entity(entity, entities):
    # translate targets defined in terms of entities, into morphological units
    # works recurrently
    targets = entity["targets"]
    resolved = []
    for target in targets:
        if target.startswith("named_"):
            target_entity = entities[target]
            resolved.extend(resolve_entity(target_entity, entities))
        else:
            resolved.append(target)
    return resolved


def eliminate_overlapping_entities(entities_list):
    # we eliminate entities which are at least partially contained in one ocurring prior to them
    # this amounts to removing overlap
    subsumed = set([])
    for sub_i, sub in enumerate(entities_list):
        for over in entities_list[:sub_i]:
            if any([target in over["targets"] for target in sub["targets"]]):
                subsumed.add(sub["ent_id"])
    return [entity for entity in entities_list if entity["ent_id"] not in subsumed]


def assign_entities(subfolder, subfolder_entities, nkjp_dir):
    # recovers all the segments from a subfolder, and annotates it with NER
    morph_path = os.path.join(nkjp_dir, subfolder, MORPH_FILE)
    rt = parse_xml(morph_path)
    morph_pars = rt.xpath("x:TEI/x:text/x:body/x:p", namespaces=NAMESPACES)
    par_id_to_segs = {}
    for par in morph_pars:
        _, par_id = get_node_id(par).split("_")
        morph_sents = par.xpath("x:s", namespaces=NAMESPACES)
        sent_id_to_segs = {}
        for morph_sent in morph_sents:
            _, sent_id = get_node_id(morph_sent).split("_")
            segs = morph_sent.xpath("x:seg", namespaces=NAMESPACES)
            sent_segs = {}
            for i, seg in enumerate(segs):
                _, seg_id = get_node_id(seg).split("morph_")
                orth = seg.xpath("x:fs/x:f[@name='orth']/x:string", namespaces=NAMESPACES)[0].text
                token = {"seg_id": seg_id,
                          "i": i,
                          "orth": orth,
                          "text": orth,
                          "tag": "_",
                          "ner": "O", # This will be overwritten
                          "ner_subtype": None,
                          }
                sent_segs[seg_id] = token
            sent_id_to_segs[sent_id] = sent_segs
        par_id_to_segs[par_id] = sent_id_to_segs

    for par_key in subfolder_entities:
        par_ents = subfolder_entities[par_key]
        for sent_key in par_ents:
            sent_entities = par_ents[sent_key]
            for entity in sent_entities:
                targets = entity["targets"]
                iob = "B"
                ner_label = entity["ner_type"]
                matching_tokens = sorted([par_id_to_segs[par_key][sent_key][target] for target in targets], key=lambda x:x["i"])
                for token in matching_tokens:
                    full_label = f"{iob}-{ner_label}"
                    token["ner"] = full_label
                    token["ner_subtype"] = entity["ner_subtype"]
                    iob = "I"
    return par_id_to_segs


def load_xml_nkjp(nkjp_dir):
    subfolder_to_annotations = {}
    for subfolder in tqdm([name for name in os.listdir(nkjp_dir) if os.path.isdir(os.path.join(nkjp_dir, name))]):
        out = extract_entities_from_subfolder(subfolder, nkjp_dir)
        if out:
            subfolder_to_annotations[subfolder] = out
        else:
            print(subfolder, "has no ann_named.xml file")

    return subfolder_to_annotations


def split_dataset(dataset, shuffle=True, train_fraction=0.9, dev_fraction=0.05, test_section=True):
    random.seed(987654321)
    if shuffle:
        random.shuffle(dataset)

    if not test_section:
        dev_fraction = 1 - train_fraction

    train_size = int(train_fraction * len(dataset))
    dev_size = int(dev_fraction * len(dataset))
    train = dataset[:train_size]
    dev = dataset[train_size: train_size + dev_size]
    test = dataset[train_size + dev_size:]

    return {
        'train': train,
        'dev': dev,
        'test': test
    }


def convert_nkjp(nkjp_dir, output_dir):
    """Converts NKJP NER data into IOB json format.

    nkjp_dir is the path to directory where NKJP files are located.
    """
    # Load XML NKJP
    subfolder_to_entities = load_xml_nkjp(nkjp_dir)
    converted = []
    for subfolder_name, pars in subfolder_to_entities.items():
        for par_id, par in pars.items():
            paragraph_identifier = f"{subfolder_name}|{par_id}"
            par_tokens = []
            for _, sent in par.items():
                tokens = sent.values()
                srt = sorted(tokens, key=lambda tok:tok["i"])
                for token in srt:
                    _ = token.pop("i")
                    _ = token.pop("seg_id")
                    par_tokens.append(token)
            par_tokens[0]["paragraph_id"] = paragraph_identifier
            converted.append(par_tokens)

    split = split_dataset(converted)

    for split_name, split in split.items():
        if split:
            with open(os.path.join(output_dir, f"pl_nkjp.{split_name}.json"), "w", encoding="utf-8") as f:
                json.dump(split, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, default="NKJP", help="Where to find the files")
    parser.add_argument('--output_path', type=str, default="data/ner", help="Where to output the results")
    args = parser.parse_args()

    convert_nkjp(args.input_path, args.output_path)


if __name__ == '__main__':
    main()
