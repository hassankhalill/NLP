"""
Text Preprocessing Module for Arabic and English Reviews
Handles cleaning, normalization, and preprocessing of multilingual text.
"""

import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
import unicodedata

# Download required NLTK data (run once)
def download_nltk_data():
    """Download required NLTK data packages."""
    packages = ['punkt', 'stopwords', 'wordnet', 'omw-1.4', 'averaged_perceptron_tagger']

    for package in packages:
        try:
            nltk.data.find(f'tokenizers/{package}' if package == 'punkt' else
                          f'corpora/{package}' if package in ['stopwords', 'wordnet', 'omw-1.4'] else
                          f'taggers/{package}')
        except LookupError:
            try:
                print(f"Downloading {package}...")
                nltk.download(package, quiet=True)
            except:
                pass  # Skip if download fails

# Initialize
try:
    download_nltk_data()
except:
    pass  # Continue even if NLTK download fails

# Arabic stopwords (common ones)
ARABIC_STOPWORDS = set([
    'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي',
    'ان', 'أن', 'إن', 'كان', 'لم', 'لن', 'قد', 'لقد', 'كل', 'بعض', 'أي', 'هو',
    'هي', 'هم', 'هن', 'أنا', 'نحن', 'أنت', 'أنتم', 'و', 'أو', 'لكن', 'لكن',
    'ثم', 'أما', 'إذا', 'لو', 'حتى', 'منذ', 'عند', 'بعد', 'قبل', 'فوق', 'تحت',
    'بين', 'خلال', 'ضد', 'نحو', 'لدى', 'لدي', 'غير', 'سوى', 'بلى', 'نعم', 'لا',
    'ليس', 'ليست', 'ليسوا', 'ما', 'ماذا', 'من', 'متى', 'أين', 'كيف', 'لماذا',
    'هل', 'الله', 'ماشاء', 'ماشاءالله', 'الحمدلله', 'سبحان'
])

# English stopwords
ENGLISH_STOPWORDS = set(stopwords.words('english'))


class TextCleaner:
    """Text cleaning and preprocessing for Arabic and English text."""

    def __init__(self, language='auto'):
        """
        Initialize TextCleaner.

        Args:
            language: 'ara', 'eng', or 'auto' for automatic detection
        """
        self.language = language
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()

    def detect_language(self, text):
        """Detect if text is primarily Arabic or English."""
        if not isinstance(text, str):
            return 'eng'

        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))

        if total_chars == 0:
            return 'eng'

        return 'ara' if arabic_chars / total_chars > 0.5 else 'eng'

    def remove_urls(self, text):
        """Remove URLs from text."""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.sub(url_pattern, '', text)

    def remove_emails(self, text):
        """Remove email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)

    def remove_mentions(self, text):
        """Remove @mentions from text."""
        return re.sub(r'@\w+', '', text)

    def remove_hashtags(self, text):
        """Remove hashtags from text."""
        return re.sub(r'#\w+', '', text)

    def remove_emojis(self, text):
        """Remove emojis from text."""
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def normalize_arabic(self, text):
        """Normalize Arabic text."""
        # Normalize Arabic letters
        text = re.sub("[إأآا]", "ا", text)
        text = re.sub("ى", "ي", text)
        text = re.sub("ؤ", "ء", text)
        text = re.sub("ئ", "ء", text)
        text = re.sub("ة", "ه", text)

        # Remove tatweel
        text = re.sub(r'ـ', '', text)

        # Remove Arabic diacritics
        arabic_diacritics = re.compile("""
            ّ    | # Tashdid
            َ    | # Fatha
            ً    | # Tanwin Fath
            ُ    | # Damma
            ٌ    | # Tanwin Damm
            ِ    | # Kasra
            ٍ    | # Tanwin Kasr
            ْ    | # Sukun
            ـ     # Tatwil/Kashida
        """, re.VERBOSE)
        text = re.sub(arabic_diacritics, '', text)

        return text

    def remove_extra_whitespace(self, text):
        """Remove extra whitespace."""
        return ' '.join(text.split())

    def remove_numbers(self, text):
        """Remove numbers from text."""
        return re.sub(r'\d+', '', text)

    def remove_punctuation(self, text, keep_arabic=True):
        """Remove punctuation."""
        if keep_arabic:
            # Remove only English punctuation
            translator = str.maketrans('', '', string.punctuation)
            return text.translate(translator)
        else:
            # Remove all punctuation
            arabic_punctuation = '؛،؟'
            all_punctuation = string.punctuation + arabic_punctuation
            translator = str.maketrans('', '', all_punctuation)
            return text.translate(translator)

    def remove_stopwords(self, text, lang='auto'):
        """Remove stopwords."""
        if lang == 'auto':
            lang = self.detect_language(text)

        tokens = word_tokenize(text)

        if lang == 'ara':
            filtered_tokens = [w for w in tokens if w not in ARABIC_STOPWORDS]
        else:
            filtered_tokens = [w for w in tokens if w.lower() not in ENGLISH_STOPWORDS]

        return ' '.join(filtered_tokens)

    def lemmatize_english(self, text):
        """Lemmatize English text."""
        tokens = word_tokenize(text)
        lemmatized = [self.lemmatizer.lemmatize(word) for word in tokens]
        return ' '.join(lemmatized)

    def stem_english(self, text):
        """Stem English text."""
        tokens = word_tokenize(text)
        stemmed = [self.stemmer.stem(word) for word in tokens]
        return ' '.join(stemmed)

    def clean_text(self, text, remove_stopwords_flag=True,
                   remove_numbers_flag=True, normalize_flag=True,
                   lemmatize_flag=False, stem_flag=False):
        """
        Complete text cleaning pipeline.

        Args:
            text: Input text to clean
            remove_stopwords_flag: Remove stopwords
            remove_numbers_flag: Remove numbers
            normalize_flag: Normalize text
            lemmatize_flag: Lemmatize English text
            stem_flag: Stem English text

        Returns:
            Cleaned text
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        # Detect language
        lang = self.detect_language(text)

        # Basic cleaning
        text = text.lower()
        text = self.remove_urls(text)
        text = self.remove_emails(text)
        text = self.remove_mentions(text)
        text = self.remove_hashtags(text)
        text = self.remove_emojis(text)

        # Normalize
        if normalize_flag:
            if lang == 'ara':
                text = self.normalize_arabic(text)

        # Remove numbers
        if remove_numbers_flag:
            text = self.remove_numbers(text)

        # Remove punctuation
        text = self.remove_punctuation(text, keep_arabic=False)

        # Remove extra whitespace
        text = self.remove_extra_whitespace(text)

        # Remove stopwords
        if remove_stopwords_flag:
            text = self.remove_stopwords(text, lang=lang)

        # Lemmatize or stem (English only)
        if lang == 'eng':
            if lemmatize_flag:
                text = self.lemmatize_english(text)
            elif stem_flag:
                text = self.stem_english(text)

        return text.strip()


def preprocess_dataframe(df, text_column='content',
                        remove_stopwords=True,
                        remove_numbers=True,
                        normalize=True,
                        lemmatize=False,
                        stem=False):
    """
    Preprocess text in a dataframe column.

    Args:
        df: Input dataframe
        text_column: Name of column containing text
        remove_stopwords: Remove stopwords
        remove_numbers: Remove numbers
        normalize: Normalize text
        lemmatize: Lemmatize English text
        stem: Stem English text

    Returns:
        DataFrame with cleaned text in new column
    """
    cleaner = TextCleaner()

    df['cleaned_text'] = df[text_column].apply(
        lambda x: cleaner.clean_text(
            x,
            remove_stopwords_flag=remove_stopwords,
            remove_numbers_flag=remove_numbers,
            normalize_flag=normalize,
            lemmatize_flag=lemmatize,
            stem_flag=stem
        )
    )

    return df


if __name__ == "__main__":
    # Fix encoding for Windows
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Test the cleaner
    cleaner = TextCleaner()

    # Test Arabic
    arabic_text = "هذا مكان جميل جداً 😍 ويوجد فيه الكثير من المعالم السياحية الرائعة!!"
    print("Original Arabic:", arabic_text)
    print("Cleaned Arabic:", cleaner.clean_text(arabic_text))
    print()

    # Test English
    english_text = "This is a beautiful place!!! Check it out at https://example.com #amazing @user"
    print("Original English:", english_text)
    print("Cleaned English:", cleaner.clean_text(english_text))
