# Transformer-based-TWG-parsing
Statistical Parsing for Tree Wrapping Grammars with Transformer-based supertagging and A-star parsing

This the repository for the experiments for the LREC 2022 submission with the title "RRGparbank: A Parallel Role and Reference Grammar Treebank"

## Installation

Install [ParTAGe-TWG](https://github.com/kawu/partage-twg).

Also install the packages from the requirements.txt file. 

The code works with the Python version 3.9

## Download language model

Here is the list of language models described in LREC paper:

- Multilingual Model:	Fine-tuned bert-base-multilingual-cased model	[download (1.7 GB)](https://www.dropbox.com/s/qmtrvieptrd13u6/best_model_mult_bert.zip?dl=0)
- English Model:	Fine-tuned bert-base-cased model	[download (1.1 GB)](https://www.dropbox.com/s/sxsbllycpennkyq/best_model_en.zip?dl=0)
- German Model:	Fine-tuned bert-base-german-cased model	[download (1.1 GB)](https://www.dropbox.com/s/pjxk6eid11zx803/best_model_de.zip?dl=0)
- French Model:	Fine-tuned camembert-base model	[download (1.1 GB)](https://www.dropbox.com/s/5t87z2ahspj7kse/best_model_fr.zip?dl=0)
- Russian Model:	Fine-tuned rubert-base-cased-sentence model	[download (1.4 GB)](https://www.dropbox.com/s/39gp9q04pbar6vw/best_model_ru.zip?dl=0)
- Multilingual DistilBERT:	Fine-tuned distilbert-base-multilingual-cased model	[download (1 GB)](https://www.dropbox.com/s/jyg8lgop5v0bktt/best_model_distilbert.zip?dl=0)

### Use downloaded model

Unzip the downloaded model and rename the folder with the unzipped model to "best_model". 


## Parse sentences

Parse a file with sentences using the file parse_twg. 

It takes two arguments - input file with plain sentences and output file. 


Please take a look at the example [input](https://github.com/TaniaBladier/Transformer-based-TWG-parsing/blob/main/example_input_file.txt) and [output](https://github.com/TaniaBladier/Transformer-based-TWG-parsing/blob/main/example_output_file.txt) files:

```
python parse_twg.py example_input_file.txt example_output_file.txt
```
The output format of the output file is discbracket (discontinuous bracket trees). Read more about this format [here](https://discodop.readthedocs.io/en/latest/fileformats.html).

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
