"""
Bilingual Text to Anki Deck Generator

Required packages:
pip install genanki deep-translator nltk

Usage:
python ankiDecksMaker.py --input <file.txt> --source-lang ru --target-lang en --deck-name "My Deck"

Arguments:
  --input: Path to input text file (required)
  --source-lang: Source language ISO 639-1 code (default: ru)
  --target-lang: Target language ISO 639-1 code (default: en)
  --deck-name: Name of the Anki deck (default: "Language Learning Deck")
  --output: Output .apkg file path (default: language_deck.apkg)
"""

import genanki
import random
import re
import argparse
from deep_translator import GoogleTranslator
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

class BilingualAnkiDeckGenerator:
    def __init__(self, input_file, source_lang='ru', target_lang='en', 
                 deck_name='Language Learning Deck', output_file="language_deck.apkg"):
        self.input_file = input_file
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.deck_name = deck_name
        self.output_file = output_file
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck = genanki.Deck(self.deck_id, deck_name)
        
        # Language name mapping for NLTK tokenization
        self.lang_map = {
            'ru': 'russian', 'en': 'english', 'es': 'spanish', 'fr': 'french',
            'de': 'german', 'it': 'italian', 'pt': 'portuguese', 'nl': 'dutch',
            'pl': 'polish', 'cs': 'czech', 'da': 'danish', 'et': 'estonian',
            'fi': 'finnish', 'el': 'greek', 'no': 'norwegian', 'sl': 'slovene',
            'sv': 'swedish', 'tr': 'turkish'
        }
        
        # Model for Source -> Target cards
        self.model_src_tgt = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            f'{source_lang.upper()} to {target_lang.upper()} Model',
            fields=[
                {'name': 'SourceWord'},
                {'name': 'SourceExample'},
                {'name': 'TargetWord'},
                {'name': 'TargetExample'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''<div style="font-size: 24px; text-align: center;">{{SourceWord}}</div>
                              <hr>
                              <div style="font-size: 18px; margin-top: 20px;">{{SourceExample}}</div>
                              <div style="margin-top: 20px;">
                                <a href="https://conjugator.reverso.net/conjugation-''' + source_lang + '''-verb-{{SourceWord}}.html" target="_blank">Conjugation</a>
                              </div>''',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue; text-align: center;">{{TargetWord}}</div>
                              <div style="font-size: 18px; margin-top: 20px;">{{TargetExample}}</div>''',
                },
            ])
        
        # Model for Target -> Source cards
        self.model_tgt_src = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            f'{target_lang.upper()} to {source_lang.upper()} Model',
            fields=[
                {'name': 'TargetWord'},
                {'name': 'SourceWord'},
                {'name': 'SourceExample'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '<div style="font-size: 24px; text-align: center;">{{TargetWord}}</div>',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue; text-align: center;">{{SourceWord}}</div>
                              <div style="font-size: 18px; margin-top: 20px;">{{SourceExample}}</div>
                              <div style="margin-top: 20px;">
                                <a href="https://conjugator.reverso.net/conjugation-''' + source_lang + '''-verb-{{SourceWord}}.html" target="_blank">Conjugation</a>
                              </div>''',
                },
            ])
        
        # Model for fill-in-the-blank cards
        self.model_cloze = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            f'{source_lang.upper()} Cloze Model',
            fields=[
                {'name': 'SourceSentence'},
                {'name': 'TargetSentence'},
                {'name': 'MissingWord'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''<div style="font-size: 20px;">{{SourceSentence}}</div>
                              <hr>
                              <div style="font-size: 18px; margin-top: 20px;">{{TargetSentence}}</div>''',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue;">{{MissingWord}}</div>''',
                },
            ])

    def read_text(self):
        """Read text from file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_words_from_sentence(self, sentence):
        """Extract words from a single sentence"""
        # Get language name for NLTK
        lang_name = self.lang_map.get(self.source_lang, 'english')
        
        try:
            words = word_tokenize(sentence, language=lang_name)
        except:
            # Fallback to basic split if language not supported
            words = sentence.split()
        
        clean_words = []
        for word in words:
            # Clean word and filter out punctuation
            clean_word = re.sub(r'[^\w]', '', word).lower()
            if len(clean_word) > 2 and clean_word.isalpha():
                clean_words.append((clean_word, word))  # (cleaned, original)
        return clean_words

    def translate_text(self, text):
        """Translate text from source to target language"""
        try:
            # Split long texts into chunks (Google Translate has limits)
            if len(text) > 500:
                return self.translator.translate(text[:500]) + "..."
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return "[Translation Error]"

    def create_cards_for_word(self, source_word, sentence):
        """Create all three card types for a single word"""
        try:
            # Translate word and sentence
            target_word = self.translate_text(source_word)
            target_sentence = self.translate_text(sentence)
            
            # 1. Source -> Target card
            note_src_tgt = genanki.Note(
                model=self.model_src_tgt,
                fields=[source_word, sentence, target_word, target_sentence],
                tags=['vocabulary', self.source_lang, self.target_lang]
            )
            
            # 2. Target -> Source card
            note_tgt_src = genanki.Note(
                model=self.model_tgt_src,
                fields=[target_word, source_word, sentence],
                tags=['vocabulary', self.source_lang, self.target_lang, 'reverse']
            )
            
            # 3. Cloze card - find the word in sentence and replace with [...]
            lang_name = self.lang_map.get(self.source_lang, 'english')
            
            try:
                words_in_sentence = word_tokenize(sentence, language=lang_name)
            except:
                words_in_sentence = sentence.split()
            
            word_to_replace = None
            for w in words_in_sentence:
                if re.sub(r'[^\w]', '', w).lower() == source_word:
                    word_to_replace = w
                    break
            
            if word_to_replace:
                sentence_with_blank = sentence.replace(word_to_replace, '[...]', 1)
                target_with_bold = target_sentence.replace(
                    target_word, f"<b>{target_word}</b>", 1
                )
                
                note_cloze = genanki.Note(
                    model=self.model_cloze,
                    fields=[sentence_with_blank, target_with_bold, source_word],
                    tags=['cloze', 'exercise', self.source_lang, self.target_lang]
                )
            else:
                note_cloze = None
            
            return note_src_tgt, note_tgt_src, note_cloze
            
        except Exception as e:
            print(f"Error creating cards for '{source_word}': {e}")
            return None, None, None

    def generate_deck(self):
        """Main method to generate the Anki deck"""
        print(f"Reading text file: {self.input_file}...")
        text = self.read_text()
        
        print(f"Tokenizing sentences (source language: {self.source_lang})...")
        lang_name = self.lang_map.get(self.source_lang, 'english')
        
        try:
            sentences = sent_tokenize(text, language=lang_name)
        except:
            # Fallback to basic sentence splitting
            sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        print(f"Found {len(sentences)} sentences")
        
        # Track words we've already seen
        seen_words = set()
        total_cards = 0
        
        # Process each sentence one by one
        for i, sentence in enumerate(sentences):
            print(f"\nProcessing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
            
            # Extract words from this sentence
            words_in_sentence = self.extract_words_from_sentence(sentence)
            
            # Find NEW words (not seen before)
            new_words = []
            for clean_word, original_word in words_in_sentence:
                if clean_word not in seen_words:
                    new_words.append(clean_word)
                    seen_words.add(clean_word)
            
            if not new_words:
                print(f"  No new words in this sentence, skipping...")
                continue
            
            print(f"  Found {len(new_words)} new word(s): {', '.join(new_words)}")
            
            # Collect all cards for this sentence
            src_tgt_cards = []
            tgt_src_cards = []
            cloze_cards = []
            
            for word in new_words:
                src_tgt_card, tgt_src_card, cloze_card = self.create_cards_for_word(word, sentence)
                
                if src_tgt_card:
                    src_tgt_cards.append(src_tgt_card)
                if tgt_src_card:
                    tgt_src_cards.append(tgt_src_card)
                if cloze_card:
                    cloze_cards.append(cloze_card)
            
            # Add cards in proper learning order:
            # First all Source -> Target
            for card in src_tgt_cards:
                self.deck.add_note(card)
                total_cards += 1
            
            # Then all Target -> Source
            for card in tgt_src_cards:
                self.deck.add_note(card)
                total_cards += 1
            
            # Finally all Cloze cards
            for card in cloze_cards:
                self.deck.add_note(card)
                total_cards += 1
        
        print(f"\n{'='*60}")
        print(f"Saving deck to {self.output_file}...")
        genanki.Package(self.deck).write_to_file(self.output_file)
        print(f"Done! Deck created successfully.")
        print(f"Deck name: {self.deck_name}")
        print(f"Source language: {self.source_lang}")
        print(f"Target language: {self.target_lang}")
        print(f"Total unique words: {len(seen_words)}")
        print(f"Total cards created: {total_cards}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Anki decks from bilingual text files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ankiDecksMaker.py --input russian_text.txt
  python ankiDecksMaker.py --input spanish.txt --source-lang es --target-lang en
  python ankiDecksMaker.py --input german.txt --source-lang de --target-lang en --deck-name "German Vocabulary"
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                        help='Path to input text file')
    parser.add_argument('--source-lang', '-s', default='ru',
                        help='Source language ISO 639-1 code (default: ru)')
    parser.add_argument('--target-lang', '-t', default='en',
                        help='Target language ISO 639-1 code (default: en)')
    parser.add_argument('--deck-name', '-d', default='Language Learning Deck',
                        help='Name of the Anki deck (default: "Language Learning Deck")')
    parser.add_argument('--output', '-o', default='language_deck.apkg',
                        help='Output .apkg file path (default: language_deck.apkg)')
    
    args = parser.parse_args()
    
    generator = BilingualAnkiDeckGenerator(
        input_file=args.input,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        deck_name=args.deck_name,
        output_file=args.output
    )
    generator.generate_deck()


if __name__ == "__main__":
    main()