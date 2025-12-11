# Anki Decks Tools
A collection of python scripts for generating Anki Decks.

## ankiDecksMaker.py
This script generates a Anki Deck from a text file.
It reads every phrase and new words are inserted as new cards.
Then also the other way around.
Finally a guess card for the word with the phrase.

It repeats that for every phrase and only new words are inserted.

### How to use
Install dependencies first.

```shell
pip install genanki deep-translator nltk
```

Insert your text inside russian_text.txt. Then just run it with

```shell
python ankiDecksMaker.py
```
