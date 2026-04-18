import pandas as pd
import docx
import PyPDF2
import re
from textblob import TextBlob


# ================= FILE READER =================
def read_text_file(file):
    name = file.name.lower()
    text = ""

    try:
        # ===== TXT =====
        if name.endswith('.txt'):
            text = file.read().decode('utf-8', errors='ignore')

        # ===== DOCX =====
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])

        # ===== PDF =====
        elif name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text()

        # ===== RTF =====
        elif name.endswith('.rtf'):
            text = file.read().decode('utf-8', errors='ignore')

        else:
            return None, None

        # 🔥 CLEAN TEXT (CONTROLLED)
        cleaned_text = smart_clean(text)

        # 🔥 PROPERTIES
        words = len(cleaned_text.split())
        chars = len(cleaned_text)
        lines = len(cleaned_text.split('\n'))

        props = {
            "words": words,
            "characters": chars,
            "lines": lines
        }

        df = pd.DataFrame({'Cleaned Text': [cleaned_text]})

        return df, props

    except Exception as e:
        print("TEXT ERROR:", e)
        return None, None


# ================= SMART CLEAN =================
def smart_clean(text):
    try:
        # 🔹 Remove extra spaces
        text = re.sub(r'\s+', ' ', text)

        # 🔹 Fix spacing around punctuation (keep symbols)
        text = re.sub(r'\s([?.!,])', r'\1', text)

        # 🔹 Split into sentences (basic)
        sentences = re.split(r'(?<=[.!?]) +', text)

        corrected_sentences = []

        for sentence in sentences:
            if len(sentence.strip()) == 0:
                continue

            # 🔥 Light correction (avoid over correction)
            blob = TextBlob(sentence)
            corrected = str(blob.correct())

            corrected_sentences.append(corrected)

        # 🔥 Join back
        final_text = " ".join(corrected_sentences)

        return final_text

    except Exception as e:
        print("CLEAN ERROR:", e)
        return text