"""
Russian Text to Anki Deck Generator

Required packages:
pip install genanki deep-translator nltk

Usage:
1. Place your Russian text in a .txt file
2. Update the input_file path in the main section
3. Run the script to generate an Anki deck (.apkg file)
"""

import genanki
import random
import re
from deep_translator import GoogleTranslator
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

class RussianAnkiDeckGenerator:
    def __init__(self, input_file, output_file="russian_deck.apkg"):
        self.input_file = input_file
        self.output_file = output_file
        self.translator = GoogleTranslator(source='ru', target='en')
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck = genanki.Deck(self.deck_id, 'Russian Learning Deck')
        
        # Model for Russian -> English cards
        self.model_ru_en = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Russian to English Model',
            fields=[
                {'name': 'Russian'},
                {'name': 'Example'},
                {'name': 'English'},
                {'name': 'EnglishExample'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''<div style="font-size: 24px; text-align: center;">{{Russian}}</div>
                              <hr>
                              <div style="font-size: 18px; margin-top: 20px;">{{Example}}</div>
                              <div style="margin-top: 20px;">
                                <a href="https://conjugator.reverso.net/conjugation-russian-verb-{{Russian}}.html" target="_blank">Conjugation</a>
                              </div>''',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue; text-align: center;">{{English}}</div>
                              <div style="font-size: 18px; margin-top: 20px;">{{EnglishExample}}</div>''',
                },
            ])
        
        # Model for English -> Russian cards
        self.model_en_ru = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'English to Russian Model',
            fields=[
                {'name': 'English'},
                {'name': 'Russian'},
                {'name': 'Example'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '<div style="font-size: 24px; text-align: center;">{{English}}</div>',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue; text-align: center;">{{Russian}}</div>
                              <div style="font-size: 18px; margin-top: 20px;">{{Example}}</div>
                              <div style="margin-top: 20px;">
                                <a href="https://conjugator.reverso.net/conjugation-russian-verb-{{Russian}}.html" target="_blank">Conjugation</a>
                              </div>''',
                },
            ])
        
        # Model for fill-in-the-blank cards
        self.model_cloze = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Russian Cloze Model',
            fields=[
                {'name': 'RussianSentence'},
                {'name': 'EnglishSentence'},
                {'name': 'MissingWord'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''<div style="font-size: 20px;">{{RussianSentence}}</div>
                              <hr>
                              <div style="font-size: 18px; margin-top: 20px;">{{EnglishSentence}}</div>''',
                    'afmt': '''{{FrontSide}}
                              <hr id="answer">
                              <div style="font-size: 24px; color: blue;">{{MissingWord}}</div>''',
                },
            ])

    def read_text(self):
        """Read Russian text from file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_words_from_sentence(self, sentence):
        """Extract words from a single sentence"""
        words = word_tokenize(sentence, language='russian')
        clean_words = []
        for word in words:
            # Clean word and filter out punctuation
            clean_word = re.sub(r'[^\w]', '', word).lower()
            if len(clean_word) > 2 and clean_word.isalpha():
                clean_words.append((clean_word, word))  # (cleaned, original)
        return clean_words

    def translate_text(self, text):
        """Translate Russian text to English"""
        try:
            # Split long texts into chunks (Google Translate has limits)
            if len(text) > 500:
                return self.translator.translate(text[:500]) + "..."
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return "[Translation Error]"

    def create_cards_for_word(self, russian_word, sentence):
        """Create all three card types for a single word"""
        try:
            # Translate word and sentence
            english_word = self.translate_text(russian_word)
            english_sentence = self.translate_text(sentence)
            
            # 1. Russian -> English card
            note_ru_en = genanki.Note(
                model=self.model_ru_en,
                fields=[russian_word, sentence, english_word, english_sentence],
                tags=['russian', 'vocabulary']
            )
            
            # 2. English -> Russian card
            note_en_ru = genanki.Note(
                model=self.model_en_ru,
                fields=[english_word, russian_word, sentence],
                tags=['russian', 'vocabulary', 'reverse']
            )
            
            # 3. Cloze card - find the word in sentence and replace with [...]
            # Try to find the original word form in the sentence
            words_in_sentence = word_tokenize(sentence, language='russian')
            word_to_replace = None
            for w in words_in_sentence:
                if re.sub(r'[^\w]', '', w).lower() == russian_word:
                    word_to_replace = w
                    break
            
            if word_to_replace:
                sentence_with_blank = sentence.replace(word_to_replace, '[...]', 1)
                english_with_bold = english_sentence.replace(
                    english_word, f"<b>{english_word}</b>", 1
                )
                
                note_cloze = genanki.Note(
                    model=self.model_cloze,
                    fields=[sentence_with_blank, english_with_bold, russian_word],
                    tags=['russian', 'cloze', 'exercise']
                )
            else:
                note_cloze = None
            
            return note_ru_en, note_en_ru, note_cloze
            
        except Exception as e:
            print(f"Error creating cards for '{russian_word}': {e}")
            return None, None, None

    def generate_deck(self):
        """Main method to generate the Anki deck"""
        print("Reading text file...")
        text = self.read_text()
        
        print("Tokenizing sentences...")
        sentences = sent_tokenize(text, language='russian')
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
            ru_en_cards = []
            en_ru_cards = []
            cloze_cards = []
            
            for word in new_words:
                ru_en_card, en_ru_card, cloze_card = self.create_cards_for_word(word, sentence)
                
                if ru_en_card:
                    ru_en_cards.append(ru_en_card)
                if en_ru_card:
                    en_ru_cards.append(en_ru_card)
                if cloze_card:
                    cloze_cards.append(cloze_card)
            
            # Add cards in proper learning order:
            # First all Russian -> English
            for card in ru_en_cards:
                self.deck.add_note(card)
                total_cards += 1
            
            # Then all English -> Russian
            for card in en_ru_cards:
                self.deck.add_note(card)
                total_cards += 1
            
            # Finally all Cloze cards
            for card in cloze_cards:
                self.deck.add_note(card)
                total_cards += 1
        
        print(f"\n{'='*50}")
        print(f"Saving deck to {self.output_file}...")
        genanki.Package(self.deck).write_to_file(self.output_file)
        print(f"Done! Deck created successfully.")
        print(f"Total unique words: {len(seen_words)}")
        print(f"Total cards created: {total_cards}")


if __name__ == "__main__":
    # Example usage
    input_file = "russian_text.txt"  # Change this to your file path
    output_file = "russian_deck.apkg"
    
    generator = RussianAnkiDeckGenerator(input_file, output_file)
    generator.generate_deck()