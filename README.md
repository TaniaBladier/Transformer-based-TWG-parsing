# Transformer-based-TWG-parsing
Statistical Parsing for Tree Wrapping Grammars with Transformer-based supertagging and A-star parsing

## Installation

Install [ParTAGe-TWG](https://github.com/kawu/partage-twg).

_Optionally, you can also install [discodop](https://github.com/andreasvc/disco-dop) This package is used as a library stored in folder discodop_n._

Also install the packages from the requirements.txt file. 

The code works with the Python version 3.9

## Download language model

Download a language model from the [RRG parser website](https://rrgparser.phil.hhu.de/parser/downloads).

Unzip the downloaded model and rename the folder to "best_model". 

Please note that for the French model you need to rename the model name from "bert" to "camembert":

```
language_model = NERModel(
    "bert", "best_model", use_cuda=device # for French, replace "bert" with "camembert"
)
```

## Parse sentences

Parse a file with sentences using the following command:

```
python reuse_saved_model.py example_input_file.txt example_output_file.txt
```
