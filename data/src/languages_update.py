#!/usr/bin/env python
"""Updates languages.json

This module takes the data/tsv directory as input and returns an
updated version of languages.json, where the script entry for each
language is updated to include every orthographic script present
in each language's tsv file. Script entries are also updated
to reflect such that script key entries match ISO 15924 aliases.
"""

import collections
import json
import operator
import os

from typing import Dict, DefaultDict, Optional

import unicodedataplus  # type: ignore

from data.src.codes import LANGUAGES_PATH, TSV_DIRECTORY_PATH  # type: ignore


def _detect_best_script_name(
    word: str,
    strict: bool = True,
) -> Optional[str]:
    """Returns the most likely script name (rather than ISO 15924 code) the
    word belongs to along with the corresponding confidence expressed as a
    maximum likelihood estimate computed over the `word` sample. If `strict`
    is enabled, then all the characters must belong to the same script and
    `(None, None)` is returned on failure.

    Example: "ژۇرنال" -> ("Arabic", 1.0).
    """
    script_counts: DefaultDict[
        str,
        float,
    ] = collections.defaultdict(float)
    for char in word:
        script_counts[unicodedataplus.script(char)] += 1.0
    script_probs = [
        (
            s,
            script_counts[s] / len(word),
        )
        for s in script_counts
    ]
    script_probs.sort(
        key=operator.itemgetter(1),
        reverse=True,
    )
    if strict and len(script_probs) != 1:
        return None
    else:
        # The script names in Unicode data tables have underscores instead of
        # whitespace to enable parsing. See:
        # https://www.unicode.org/Public/13.0.0/ucd/Scripts.txt
        return script_probs[0][0]


def _get_alias(
    value: str,
) -> str:
    """Takes a script ID string from _detect_best_script_name()
    and returns the ISO 15924 code alias for that script.

    Example: "Arabic" -> "arab"
    """
    return "".join(
        unicodedataplus.property_value_aliases["script"][value]
    ).lower()


def _remove_mismatch_ids(
    script_dict: Dict[
        str,
        Dict[
            str,
            str,
        ],
    ]
) -> Dict[str, Dict[str, str]]:
    """Removes [key:value] pairs when the key does not
    match the ISO 15924 code alias for script.
    """
    remove = []
    for (
        key,
        value,
    ) in script_dict["script"].items():
        value = value.replace(
            " ",
            "_",
        )
        if _get_alias(value) != key:
            remove.append(key)
    for i in remove:
        del script_dict["script"][i]
    return script_dict


def _update_languages_json(
    tsv_path: str,
    output_path: str,
) -> None:
    """Detects and identifies all unicode scripts present in a tsv file
    and updates languages.json to reflect updated ["script"]
    entries for each language in languages.json
    """
    with open(
        LANGUAGES_PATH,
        "r",
        encoding="utf-8",
    ) as lang_source:
        languages = json.load(lang_source)
        for file in os.listdir(tsv_path):
            if file.endswith(".tsv"):
                iso639_code = file[: file.index("_")]
                lang = languages[iso639_code]
                with open(
                    f"{tsv_path}/{file}",
                    "r",
                    encoding="utf-8",
                ) as f:
                    for line in f:
                        if line is not None:
                            word = line.split(
                                "\t",
                                1,
                            )[0]
                            script = _detect_best_script_name(word)
                            if script is not None:
                                if "script" not in lang:
                                    lang["script"] = {}
                                # Uses property_value_aliases to get
                                # ISO-15924 code.
                                if script not in lang["script"]:
                                    lang["script"][
                                        _get_alias(script)
                                    ] = script.replace(
                                        "_",
                                        " ",
                                    )
                            _remove_mismatch_ids(lang)
        json_object = json.dumps(
            languages,
            ensure_ascii=False,
            indent=4,
        )
        with open(
            LANGUAGES_PATH,
            "w",
            encoding="utf-8",
        ) as lang_source:
            lang_source.write(json_object)


def main():
    _update_languages_json(
        TSV_DIRECTORY_PATH,
        LANGUAGES_PATH,
    )


if __name__ == "__main__":
    main()
