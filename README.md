# Transformer-based-TWG-parsing
Statistical Parsing for Tree Wrapping Grammars with Transformer-based supertagging and A-star parsing

## Installation

Install [ParTAGe-TWG](https://github.com/kawu/partage-twg).

_Optionally, you can also install [discodop](https://github.com/andreasvc/disco-dop). This package is used as a library stored in folder discodop_n._

Also install the packages from the requirements.txt file. 

The code works with the Python version 3.9

## Download language model

Download a language model from the [RRG parser website](https://rrgparser.phil.hhu.de/parser/downloads).

Unzip the downloaded model and rename the folder with the unzipped model to "best_model". 

Please note that for the French model you need to rename the model name from "bert" to "camembert":

```
language_model = NERModel(
    "bert", "best_model", use_cuda=device # for French, replace "bert" with "camembert"
)
```

To use DistilBERT model, rename the model name from "bert" to "distilbert":


```
language_model = NERModel(
    "distilbert", "best_model", use_cuda=device 
)
```

## Parse sentences

Parse a file with sentences using the file parse_twg. 

It takes two arguments - input file with plain sentences and output file. 

Please take a look at the example files:

```
python parse_twg.py example_input_file.txt example_output_file.txt
```
