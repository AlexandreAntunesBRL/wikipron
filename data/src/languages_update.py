#!/usr/bin/env python

import collections
import json
import operator
import os
import sys

import unicodedataplus
from data.src.codes import LANGUAGES_PATH, TSV_DIRECTORY_PATH

from typing import Dict, Tuple, Union

def _detect_best_script_name(
    word: str, strict: bool = True
) -> Union[Tuple[str, float], None]:
    """Returns the most likely script name (rather than ISO 15924 code) the
    word belongs to along with the corresponding confidence expressed as a
    maximum likelihood estimate computed over the `word` sample. If `strict`
    is enabled, then all the characters must belong to the same script and
    `(None, None)` is returned on failure.

    Example: "ژۇرنال" -> ("Arabic", 1.0).
    """
    script_counts: Dict[str, float] = collections.defaultdict(float)
    for char in word:
        script_counts[unicodedataplus.script(char)] += 1.0
    script_probs = [(s, script_counts[s] / len(word)) for s in script_counts]
    script_probs.sort(key=operator.itemgetter(1), reverse=True)
    if strict and len(script_probs) != 1:
        return None
    else:
        # The script names in Unicode data tables have underscores instead of
        # whitespace to enable parsing. See:
        #   https://www.unicode.org/Public/13.0.0/ucd/Scripts.txt
        return script_probs[0][0], script_probs[0][1]


def _remove_duplicates(script_dict: Dict[str, str]) -> Dict[str, str]:
    '''
    If a values in lang["script"] appears more than once, the [key:value] pair that does not conform to ISO unicode
    entries returned from unicodedataplus.property_value_aliases['script'] is deleted.

    eg)

    "aze": {
        "iso639_name": "Azerbaijani",
        "wiktionary_name": "Azerbaijani",
        "wiktionary_code": "az",
        "casefold": true,
        "script": {
            "latn": "Latin",
            "cyrl": "Cyrillic",
            "ara": "Arabic",
            "arab": "Arabic"
        }

        ->

        "aze": {
        "iso639_name": "Azerbaijani",
        "wiktionary_name": "Azerbaijani",
        "wiktionary_code": "az",
        "casefold": true,
        "script": {
            "latn": "Latin",
            "cyrl": "Cyrillic",
            "arab": "Arabic"
        }


    '''
    remove = []

    for key, value in script_dict["script"].items():
        value = value.replace(" ", "_")
        if not ''.join(unicodedataplus.property_value_aliases['script'][value]).lower() == key:
            remove.append(key)
    for i in remove:
        del script_dict["script"][i]
    return script_dict


def _update_languages_json(tsv_path: str, output_path: str) -> None:
    '''
    Detects and identifies all unicode scripts present in a tsv file
    and updates languages.json to reflect updated ["script"]
    entries for each language in languages.json
    '''
    with open(LANGUAGES_PATH, "r", encoding="utf-8") as lang_source:
        languages = json.load(lang_source)
        for file in os.listdir(tsv_path):
            if file.endswith('.tsv'):
                iso639_code = file[:file.index("_")]
                lang = languages[iso639_code]
                with open(f'{tsv_path}/{file}', "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            word = line.split("\t", 1)[0]
                            script, prob = _detect_best_script_name(word)
                            if not "script" in lang:
                                lang["script"] = {}
                            # use property_value_aliases to get ISO 15924 code
                            if not script in lang["script"]:
                                lang["script"][''.join(
                                    unicodedataplus.property_value_aliases['script'][script]).lower()] = script.replace(
                                    "_", " ")
                            _remove_duplicates(lang)
                        except TypeError as error:
                            pass
        json_object = json.dumps(languages, indent=4)

        with open(output_path, "w", encoding="utf-8") as lang_source:
            lang_source.write(json_object)


def main():
    '''
    Create a dummy file that will show how languages.json will be updated if split.py is executed
    '''
    output_path = sys.argv[1]

    _update_languages_json(TSV_DIRECTORY_PATH, output_path)


if __name__ == "__main__":
    main()